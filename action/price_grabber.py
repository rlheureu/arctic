'''
Created on May 9, 2017

@author: shanrandhawa
'''
import logging
import os

import bottlenose
from bs4 import BeautifulSoup

from database import dataaccess
from database.database import db
from models.models import BaseComponent, GPUComponent, MotherboardComponent, \
    ComponentPrice, MemoryComponent
from utils import retry_util, retaildata_utils
from datetime import datetime

LOG = logging.getLogger('app')

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
    
    def _product_type_names(self):
        raise NotImplementedError('Call subclass')
    
    def _item_type_further_confirmation(self, item):
        return True
    
    def fetch_3p_item_info(self, item3pid):
        
        rawxml = retry_util.retry_func(3, 2, self.amazon.ItemLookup, ItemId=item3pid, ResponseGroup='ItemAttributes,Offers')
        
        bs = BeautifulSoup(rawxml, 'html.parser')
        
        item = bs.find('item')
        if not item: return None
        
        info = ItemInfo3p()
        info.title = item.title.string
        info.url = item.detailpageurl.string
        info.rawdata = item
        
        return info
    
    def _populate_component(self, item, component):
        
        if not item.producttypename.string in self._product_type_names(): return None
        
        if not self._item_type_further_confirmation(item): return None
        
        attrmap = self._get_attribute_mapping()
        
        """ set the easy components based on the mapping provided by subclass """
        for mk, mv in attrmap.items():
            
            itemval = getattr(item, mk).string if getattr(item, mk) else None
            
            """ update the component if that value does not exist (i.e. do not overwrite) """
            if itemval and not getattr(component, mv): setattr(component, mv, itemval)
        
        """ set any stuff that requires more knowledge on this particular part type """
        self._extract_addl_attributes(item, component)
        
        """ set UPC & ASIN """
        if not component.upc and item.upc: component.upc = item.upc.string
        if not component.asin: component.asin = item.asin.string
        
        return component
        
    def _filter_existing_components(self, item_list):
        
        newcomps = {}
        
        for item in item_list:
            
            if not item.asin:
                continue
            
            asin = item.asin.string
            
            component = dataaccess.get_component_by_asin(asin, active_only=False)
            
            if not component: newcomps[asin] = item
            
        return newcomps.values()

    def _discover(self, searchcriteria, max_items, existing, update_existing):
        
        rawxml = retry_util.retry_func(3, 5, self.amazon.ItemSearch, Keywords=searchcriteria.keywords, SearchIndex="PCHardware", ResponseGroup='ItemAttributes,Offers')
        bs = BeautifulSoup(rawxml, 'html.parser')
        items = bs.find_all('item')
        
        """ amazon returns 10 items per page, do another search if there are more pages """
        itemcount = len(items)
        pagenum = 1
        while itemcount < max_items:
            if bs.find('totalpages') and int(bs.find('totalpages').string) > pagenum:
                pagenum += 1
                rawxml = retry_util.retry_func(3, 5, self.amazon.ItemSearch, Keywords=searchcriteria.keywords, SearchIndex="PCHardware", ResponseGroup='ItemAttributes,Offers', ItemPage=pagenum)
                bs = BeautifulSoup(rawxml, 'html.parser')
                items += bs.find_all('item')
                itemcount = len(items)
            else:
                break
        
        newitems = self._filter_existing_components(items)
        
        count_added = 0
        for item in newitems:
            
            """ do not discover parts that are not available """
            if int(item.offers.totaloffers.string) < 1: continue
            
            component = self._populate_component(item, existing if update_existing else self._init_component())
            if not component: continue
            
            if count_added >= max_items: break
            
            """ set status as auto populated and created """
            if component.auto_populated is None: component.auto_populated = True
            if not component.use_status: component.use_status = BaseComponent.Status.CREATED 
            db.session().add(component)
            count_added += 1
        
        db.session().flush()
        db.session().commit()
        
    def _findupdate(self, component_list):
        
        for comp in component_list:
            
            if not comp.asin: continue
            
            iteminfo = self.fetch_3p_item_info(comp.asin)
            
            if not iteminfo: continue
            
            iteminforaw = iteminfo.rawdata
            
            if not iteminfo:
                """ this would happen if the item no longer exists or is available """
                """ for now I guess we can skip """
                continue
            
            
            """ delete all prices for this component from amazon """
            for cprice in comp.prices:
                if not cprice.retailer or cprice.retailer.name.lower() == 'amazon':
                    db.session().delete(cprice)
            
            """
            now extract pricing information and create/update pricing records
            """
            offerinfolist = iteminforaw.find_all('offer')
            
            if len(offerinfolist) < 1:
                comp.available = False
                db.session().add(comp)
                db.session().flush()
                db.session().commit()
                continue
            
            offerinfo = offerinfolist[0]
            
            compprice = ComponentPrice()
            compprice.auto_populated = True
            compprice.component = comp
            compprice.foreign_id = comp.asin
            compprice.link = iteminforaw.detailpageurl.string
            compprice.price = int(offerinfo.offerlisting.price.amount.string)
            compprice.formatted_price = offerinfo.offerlisting.price.formattedprice.string
            compprice.retailer = dataaccess.get_retailer_by_name('amazon')
            compprice.use_status = comp.use_status
            compprice.updated_at = datetime.now()
            
            comp.available = True
            
            db.session().add(compprice)
            db.session().flush()
            db.session().commit()
            
            
        
        
class AmazonGPUExtractor(AmazonExtractor):
    
    def _product_type_names(self):
        return ['VIDEO_CARD']
    
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
    
    def _product_type_names(self):
        return ['MOTHERBOARD']
    
    def _init_component(self):
        return MotherboardComponent()
    
    def _get_attribute_mapping(self):
        return {
                'brand' : 'brand_name',
                'model' : 'model_number',
                'title' : 'display_name'
                }
    
    def _extract_addl_attributes(self, item, component):
        pass      
        
class AmazonMemoryExtractor(AmazonExtractor):
    
    def _product_type_names(self):
        return ['RAM_MEMORY', 'COMPUTER_COMPONENT']
    
    def _init_component(self):
        return MemoryComponent()
    
    def _item_type_further_confirmation(self, item):
        titlestr = item.title.string
        if 'sodimm' in titlestr.lower(): return False
        if 'so-dimm' in titlestr.lower(): return False
        
        """ confirm other required params are available """
        
        if retaildata_utils.sticks_and_capacity(titlestr) and retaildata_utils.memtype(titlestr) and retaildata_utils.memory_frequency(titlestr):
            return True
        else:
            'skipping ' + titlestr
            
        return False
    
    def _get_attribute_mapping(self):
        return {
                'brand' : 'brand_name',
                'manufacturer' : 'vendor',
                'model' : 'model_number',
                'title' : 'display_name'
                }
    
    def _extract_addl_attributes(self, item, component):
        titlestr = item.title.string
        sticksandcap = retaildata_utils.sticks_and_capacity(titlestr)
        component.memory_capacity = sticksandcap[0] * sticksandcap[1]
        component.dimms = sticksandcap[0]
        component.memory_frequency = retaildata_utils.memory_frequency(titlestr)
        component.memory_spec = retaildata_utils.memtype(titlestr)

class SearchCriteria:
    pass

def sync_prices():
    
    
    complists = [dataaccess.get_all_cpus(False, None),
                 dataaccess.get_all_gpus(False, None),
                 dataaccess.get_all_mobos(False, None),
                 dataaccess.get_all_memory(False, None),
                 dataaccess.get_all_displays(False, None),
                 dataaccess.get_all_chassis(False, None),
                 dataaccess.get_all_power(False, None),
                 dataaccess.get_all_storage(False, None)]
    
    for complist in complists:
        LOG.info('Running sync prices on {} components'.format(len(complist)))
        AmazonExtractor().find_and_update_offers(complist)
        
    

def run_discovery():
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
    #mobos = dataaccess.get_all_mobos()
    #count=0
    #for mobo in mobos:
    #    count+=1
    #    sc = SearchCriteria()
    #    sc.keywords = mobo.brand_name
    #    AmazonMotherboardExtractor().discover_components(sc, 1, mobo, True)
    #    
    #    if count % 10 == 0: print 'Discovery Process: Completed {}/{}'.format(count, len(mobos))
    
    
    
    #sc = SearchCriteria()
    #sc.keywords = 'Memory'
    #AmazonMemoryExtractor().discover_components(sc, 500)
    #c.keywords = 'RAM'
    #AmazonMemoryExtractor().discover_components(sc, 500)
    #sc.keywords = 'DDR3'
    #AmazonMemoryExtractor().discover_components(sc, 500)
    #sc.keywords = 'DDR4'
    #AmazonMemoryExtractor().discover_components(sc, 500)
    
    
    


