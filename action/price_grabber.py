'''
Created on May 9, 2017

@author: shanrandhawa
'''
import os

import bottlenose
from bs4 import BeautifulSoup

from database import dataaccess
from database.database import db
from models.models import BaseComponent, GPUComponent, MotherboardComponent
from utils import retry_util

class ItemInfo3p:
    """
    standardized 3P item object
    """
    pass

class BaseExtractor:
    
    def _findupdate(self, component_list):
        raise NotImplementedError('Call subclass')
    
    def _discover(self, searchcriteria, max_items, existing, update_existing):
        raise NotImplementedError('Call subclass')
    
    def find_and_update_offers(self, component_list):
        """
        This method will update prices for each of the components passed in
        """
        return self._findupdate(component_list)
    
    def fetch_3p_item_info(self, item3pid):
        """
        Will connect with third party retailer and fetch info about item
        """
        raise NotImplementedError('call subclass')
    
    def discover_components(self, searchcriteria, max_items=20, existing=None, update_existing=False):
        """
        This method will fetch a list of 20 parts matching the search term
        and park them in the database for further review
        """
        
        if update_existing and not existing:
            raise ValueError('Update existing cannot be done without an existing component being passed in.')
        
        return self._discover(searchcriteria, max_items, existing, update_existing)
    

class AmazonExtractor(BaseExtractor):
    
    amazon = bottlenose.Amazon(os.environ['AWS_AFFILIATE_KEY'], os.environ['AWS_AFFILIATE_SECRET'], os.environ['AWS_ASSOCIATE_TAG'])
    
    def _init_component(self):
        raise NotImplementedError('Call subclass')
    
    def _get_attribute_mapping(self):
        raise NotImplementedError('Call subclass')
    
    def _extract_addl_attributes(self, item, component):
        raise NotImplementedError('Call subclass')
    
    def _product_type_name(self):
        raise NotImplementedError('Call subclass')
    
    def _matches_existing(self, existing_component, item):
        raise NotImplementedError('Call subclass')
    
    def fetch_3p_item_info(self, item3pid):
        
        rawxml = retry_util.retry_func(3, 2, self.amazon.ItemLookup, ItemId=item3pid)
        
        bs = BeautifulSoup(rawxml, 'html.parser')
        
        item = bs.find('item')
        if not item: return None
        
        info = ItemInfo3p()
        info.title = item.title.string
        info.url = item.detailpageurl.string
        
        return info
    
    def _populate_component(self, item, component):
        
        if not item.upc: return None
        if item.producttypename.string != self._product_type_name():
            return None
        
        attrmap = self._get_attribute_mapping()
        
        """ set the easy components based on the mapping provided by subclass """
        for mk, mv in attrmap.items():
            
            itemval = getattr(item, mk).string if getattr(item, mk) else None
            
            """ update the component if that value does not exist (i.e. do not overwrite) """
            if itemval and not hasattr(component, mv): setattr(component, mv, itemval)
        
        """ set any stuff that requires more knowledge on this particular part type """
        self._extract_addl_attributes(item, component)
        
        """ set UPC & ASIN """
        if not component.upc: component.upc = item.upc.string
        if not component.asin: component.asin = item.asin.string
        
        return component
        
    def _filter_existing_components(self, item_list):
        
        newcomps = []
        
        for item in item_list:
            
            if not item.itemattributes.upc:
                """ unfortunately, if there's no UPC we cannot use this product for now """
                continue
            
            upc = item.itemattributes.upc.string
            
            component = dataaccess.get_component_by_upc(upc)
            
            if not component: newcomps.append(item)
            
        return newcomps    

    def _discover(self, searchcriteria, max_items, existing, update_existing):
        
        rawxml = retry_util.retry_func(3, 5, self.amazon.ItemSearch, Keywords=searchcriteria.keywords, SearchIndex="PCHardware", ResponseGroup='ItemAttributes,Offers')
        bs = BeautifulSoup(rawxml, 'html.parser')
        items = bs.find_all('item')
        
        """ amazon returns 10 items per page, do another search if there are more pages """
        itemcount = len(items)
        while itemcount < max_items:
            if int(bs.find('totalpages').string) > 1:
                rawxml = retry_util.retry_func(3, 5, self.amazon.ItemSearch, Keywords=searchcriteria.keywords, SearchIndex="PCHardware", ResponseGroup='ItemAttributes,Offers', ItemPage=2)
                bs = BeautifulSoup(rawxml, 'html.parser')
                items += bs.find_all('item')
                itemcount = len(items)
            else:
                break
        
        newitems = self._filter_existing_components(items)
        
        count_added = 0
        for item in newitems:
            
            component = self._populate_component(item, existing if update_existing else self._init_component())
            if not component: continue
            
            if count_added >= max_items: break
            
            """ set status as auto populated and created """
            if component.auto_populated is None: component.auto_populated = True
            if not component.use_status: component.use_status = BaseComponent.Status.CREATED 
            db.session().add(component)
            count_added += 1
        
        db.session().commit()
        
        
class AmazonGPUExtractor(AmazonExtractor):
    
    def _product_type_name(self):
        return 'VIDEO_CARD'
    
    def _init_component(self):
        return GPUComponent()
    
    def _get_attribute_mapping(self):
        return {
                'brand' : 'brand_name',
                'model' : 'model_number',
                'title' : 'display_name'
                }
    
    def _extract_addl_attributes(self, item, component):
        pass

class AmazonMotherboardExtractor(AmazonExtractor):
    
    def _product_type_name(self):
        return 'MOTHERBOARD'
    
    def _init_component(self):
        return MotherboardComponent()
    
    def _matches_existing(self, existing_component, item):
        pass
    
    def _get_attribute_mapping(self):
        return {
                'brand' : 'brand_name',
                'model' : 'model_number',
                'title' : 'display_name'
                }
    
    def _extract_addl_attributes(self, item, component):
        pass      
        

class SearchCriteria:
    pass

def get_3p_prices():
    """
    will call all retailer APIs and do the following:
    - get any updates on pricing for existing products
    """

    


    #gpulist = dataaccess.get_all_gpus()
    #print 'running discovery process for {} items.'.format(len(gpulist))
    #count = 0
    #for gpu in gpulist:
        
    #    sc = SearchCriteria()
    #    sc.keywords = gpu.vendor + ' ' + gpu.model_number
    #    AmazonGPUExtractor().discover_components(sc)
        
    #    count+=1
    #    if count % 10 == 0: print 'Discovery Process: Completed {}/{}'.format(count, len(gpulist))
    
    
    """
    motherboards - no discovery since we already have actual parts in DB
    """
    mobos = dataaccess.get_all_mobos()
    count=0
    for mobo in mobos:
        count+=1
        sc = SearchCriteria()
        sc.keywords = mobo.brand_name
        AmazonMotherboardExtractor().discover_components(sc, 1, mobo, True)
        
        if count % 10 == 0: print 'Discovery Process: Completed {}/{}'.format(count, len(mobos))
        
    
    
    


