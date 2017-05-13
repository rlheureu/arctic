'''
Created on May 3, 2017

@author: shanrandhawa


recommendations service

'''

import logging

from database import dataaccess
from models.models import BaseComponent
from utils import retaildata_utils


LOG = logging.getLogger('app')

class RecResponse: pass

def determine_cheapest_comp(comps):
    cheapest = None
    for comp in comps:
        price = lowest_price(comp.prices)
        if not price: continue
        comp.price=price
        comp.formattedprice = price.formatted_price
        comp.buyurl = price.link
        
        if not cheapest: cheapest = comp
        elif comp.price.price < cheapest.price.price: cheapest = comp
        
    return cheapest

def generate_memory_config_recommendations(memlist):
    recommendmap = {}
    for mem in memlist:
        price = lowest_price(mem.prices)
        if not price: continue
        mem.price = price
        mem.formattedprice = price.formatted_price
        mem.buyurl = price.link
        
        memcfgs = [2]
        if mem.dimms > 2: memcfgs.append(4)
        
        memspec = mem.memory_spec if mem.memory_spec in ['DDR3', 'DDR4'] else None
        if not memspec: continue
        
        memcap = mem.memory_capacity
        capcfgs = ['4GB']
        if memcap < 4: continue
        if memcap >= 8: capcfgs.append('8GB')
        
        for dimmcfg in memcfgs:
            for capcfg in capcfgs:
                mkey = '{}-{}-{}'.format(memspec,dimmcfg,capcfg)
                val = recommendmap.get(mkey)
                if not val: recommendmap[mkey] = mem
                elif price.price < val.price.price: recommendmap[mkey] = mem
            
            mkey = '{}-{}-$/GB'.format(memspec,dimmcfg)
            val = recommendmap.get(mkey)
            if not val: recommendmap[mkey] = mem
            elif int(mem.price.price) / int(memcap) < int(val.price.price)/int(val.memory_capacity): recommendmap[mkey] = mem
    
    return recommendmap

def determine_cpu_fps_tier(cpu_comp, genres):
    """ will return the numerical performance tier and the lowest average FPS across the genres passed in """
    
    bygenre = {}
    lowest_average = None
    for datapoint in cpu_comp.fps_data:
        """ we only want to look at the first-person shooter data """
        genre = str(datapoint.benchmark_type)
        
        if not lowest_average or datapoint.fps_average < lowest_average: lowest_average = datapoint.fps_average
        
        if datapoint.fps_average >= 144: bygenre[genre] = 6
        elif datapoint.fps_average >= 120: bygenre[genre] = 5
        elif datapoint.fps_one >= 60: bygenre[genre] = 4
        elif datapoint.fps_average >= 60: bygenre[genre] = 3
        elif datapoint.fps_one >= 30: bygenre[genre] = 2
        elif datapoint.fps_average >= 30: bygenre[genre] = 1
    
    if len(bygenre.values()) == 0: return 0,None # NO DATA
    
    """ if the same set of genres are not being compared then return 0 (i.e. data is incomplete) """
    if len(set(genres).intersection(set(bygenre.keys()))) != len(set(genres)): return 0, None
    
    return min(bygenre.values()), lowest_average     

def lowest_price(prices):
    lowest = None
    for price in prices:
        if not lowest or price.price < lowest: lowest = price
    return lowest

def recommend_same_chipset_cpu(chipsets, tier, comp_genres):
    """
    args:
    - list of chipsets (strings), e.g. ['H170','Z270'],
    - the numerical performance tier,
    - the genre set to compare against
    
    """
    
    same_cs_cpus = dataaccess.get_cpus_by_chipset(chipsets, available=True)
    
    LOG.info('Generating CPU recommendation for chipsets {} got {} cpus'.format(chipsets, len(same_cs_cpus)))
    
    """ the cheapest available CPU for each tier """
    tiertocpus = {}
    topperforming = None
    lowestdollarfps = None
    for cpu in same_cs_cpus:
        ptier, lowestfps = determine_cpu_fps_tier(cpu, set(comp_genres))
        if ptier <= tier: continue
        
        """ cheapest by tier """
        price = lowest_price(cpu.prices)
        if not tiertocpus.get(ptier) or price.price < tiertocpus.get(ptier).price: tiertocpus[ptier] = cpu
        
        cpu.buyurl = price.link
        cpu.formattedprice = price.formatted_price
        cpu.price = price
        
        """ top performance """
        cpu.lowestfps = lowestfps
        if not topperforming: topperforming = cpu
        elif topperforming.lowestfps < lowestfps or (topperforming.lowestfps == lowestfps and price.price < topperforming.price.price):
            """ higher performing or if same then keep the cheaper one """
            topperforming = cpu
        
        """ lowest dollar per fps """
        dollarfps = price.price/lowestfps
        if not lowestdollarfps: lowestdollarfps = cpu
        elif dollarfps < cpu.price.price/cpu.lowestfps: dollarfps = cpu
    
    return tiertocpus, topperforming, lowestdollarfps 
         
    
def recommend_newplatform_cpu(currchipsets, tier, comp_genres):
    all_cpus = dataaccess.get_all_cpus()
    
    othercpus = []
    for cpu in all_cpus:
        """ only proceed with CPUs compatible with different chipsets """
        if not cpu.chipset_name: continue
        chipsetsoverlap = len(set(cpu.chipset_name.split(',')).intersection(currchipsets)) > 0
        if chipsetsoverlap: continue
        if determine_cpu_fps_tier(cpu, comp_genres)[0] > tier: othercpus.append(cpu)
    
    memrecs = generate_memory_config_recommendations(dataaccess.get_all_memory(available=True))
    lowestbytier = {}
    topperforming = None
    lowestdollarfps = None
    for cpu in othercpus:
        
        price = lowest_price(cpu.prices)
        if not price: continue
        
        mobos = dataaccess.get_compatible_mobo_map(cpu.id, available=True, use_status=BaseComponent.Status.APPROVED)
        cheapestmobo = determine_cheapest_comp(mobos)
        cheapestmem = memrecs.get("{}-{}-{}".format(cheapestmobo.memory_spec, cheapestmobo.dimms, "4GB"))
        cpu.recommendedmobo = cheapestmobo
        cpu.recommendedmemory = cheapestmem
        
        cpu.price = price
        cpu.platform_price = cpu.price.price + cheapestmem.price.price + cheapestmobo.price.price
        cpu.formattedplatformprice = retaildata_utils.format_int_price(cpu.platform_price)
        cpu.buyurl = price.link
        cpu.formattedprice = price.formatted_price
        
        """ cheapest by tier """
        tier, lowestfps = determine_cpu_fps_tier(cpu, comp_genres)
        if not tier or not lowestfps: continue
        val = lowestbytier.get(tier)
        if not val: lowestbytier[tier] = cpu
        elif cpu.platform_price < val.platform_price: lowestbytier[tier] = cpu
        
        """ best performance """
        cpu.lowestfps = lowestfps
        if not topperforming: topperforming = cpu
        elif topperforming.lowestfps < lowestfps or (topperforming.lowestfps == lowestfps and cpu.platform_price < topperforming.platform_price):
            """ higher performing or if same then keep the cheaper one """
            topperforming = cpu        
        
        """ lowest $/FPS """
        dollarfps = price.price/lowestfps
        if not lowestdollarfps: lowestdollarfps = cpu
        elif dollarfps < cpu.platform_price/cpu.lowestfps: dollarfps = cpu        
        
    
    return lowestbytier, topperforming, lowestdollarfps

def populate_fps_gains(currcpu, comps, genres):

    tierblurbs = {0 :'Really bad performance',
                  1 :'Gets at least 30 FPS on average',
                  2 :'Gets at least 30 FPS 99% of the time',
                  3 :'Gets at least 60 FPS on average',
                  4 :'Gets at least 60 FPS 99% of the time',
                  5 :'Gets at least 120 FPS on average',
                  6 :'Gets at least 144 FPS on average'}
    
    tier, lowestfps = determine_cpu_fps_tier(currcpu, genres)
    
    currcpu.tier = tier
    currcpu.tier_explain = tierblurbs[tier]
    
    for comp in comps:
        comptier, complowestfps = determine_cpu_fps_tier(comp, genres)
        gains = int(complowestfps - lowestfps)
        comp.fpsgain = gains
        if hasattr(comp, 'platform_price'): comp.dollarfps = comp.platform_price / 100 / gains
        else: comp.dollarfps = comp.price.price / 100 / gains
        comp.tier = comptier
        comp.tier_explain = tierblurbs[comptier]
        

def recommend_a_cpu(input_cpu, genres=[]):
    """
    returns a recommended CPU based on the inputs provided
    """
    
    """ first which tier does this CPU fall into? """
    comp_genres = genres
    for dp in input_cpu.fps_data: comp_genres.append(str(dp.benchmark_type))
    tier = determine_cpu_fps_tier(input_cpu, set(comp_genres))[0]
    
    LOG.info('the tier is ' + str(tier))
    
    """ there is no better part to recommend """
    if tier == 6: return None
    
    scs_recs, scs_top, scs_dollarfps = recommend_same_chipset_cpu(input_cpu.chipset_name.split(','), tier, comp_genres)
    np_recs, np_top, np_dollarfps = recommend_newplatform_cpu(input_cpu.chipset_name.split(','), tier, comp_genres)
    
    populate_fps_gains(input_cpu, scs_recs.values() + np_recs.values() + [scs_top,scs_dollarfps,np_top,np_dollarfps], comp_genres)
    
    res = {}
    res['scsbytier'] = scs_recs
    res['scstop'] = scs_top
    res['scsbv'] = scs_dollarfps
    res['npbytier'] = np_recs
    res['nptop'] = np_top
    res['npbv'] = np_dollarfps
    
    return res

