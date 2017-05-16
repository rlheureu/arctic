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
        
        if not mem.memory_capacity: continue
        try: memcap = int(mem.memory_capacity)
        except: continue
        
        capcfgs = []
        if memcap < 4: continue
        if memcap == 4: capcfgs.append('4GB')
        elif memcap >= 8: capcfgs.append('8GB')
        
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

def recommend_same_chipset_cpu(input_cpu, chipsets, tier, comp_genres):
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
        if cpu.id == input_cpu.id: continue
        ptier, lowestfps = determine_cpu_fps_tier(cpu, set(comp_genres))
        if ptier < tier: continue
        price = lowest_price(cpu.prices)
        if not price: continue
        
        """ cheapest by HIGHER tier """
        if ptier > tier and (not tiertocpus.get(ptier) or price.price < tiertocpus.get(ptier).price): tiertocpus[ptier] = cpu
        
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

def populate_memory_config(cpu, mobo, memrecs):         
    """
    if mobo has 4 slots it can use the cheaper option of the two
    """
    
    if mobo.dimms > 2:
        """ this mobo has 4 dimms, so pick cheapest of the 2 or 4 stick options """
        option4gb2 = memrecs.get("{}-{}-{}".format(mobo.memory_spec, 2, "4GB"))
        option4gb4 = memrecs.get("{}-{}-{}".format(mobo.memory_spec, 4, "4GB"))
        if option4gb2 and not option4gb4: cpu.recommendedmemory4gb = option4gb2
        elif not option4gb2 and option4gb4: cpu.recommendedmemory4gb = option4gb4
        elif option4gb2 and option4gb4: cpu.recommendedmemory4gb = option4gb2 if option4gb2.price.price < option4gb4.price.price else option4gb4
        
        option8gb2 = memrecs.get("{}-{}-{}".format(mobo.memory_spec, 2, "8GB"))
        option8gb4 = memrecs.get("{}-{}-{}".format(mobo.memory_spec, 4, "8GB"))
        if option8gb2 and not option8gb4: cpu.recommendedmemory8gb = option8gb2
        elif not option8gb2 and option8gb4: cpu.recommendedmemory8gb = option8gb4
        elif option8gb2 and option8gb4: cpu.recommendedmemory8gb = option8gb2 if option8gb2.price.price < option8gb4.price.price else option8gb4
        
    else:
        option4gb2 = memrecs.get("{}-{}-{}".format(mobo.memory_spec, 2, "4GB"))
        if option4gb2: cpu.recommendedmemory4gb = option4gb2
        option8gb2 = memrecs.get("{}-{}-{}".format(mobo.memory_spec, 2, "8GB"))
        if option8gb2: cpu.recommendedmemory8gb = option8gb2
    
    
def recommend_newplatform_cpu(input_cpu, currchipsets, tier, comp_genres):
    all_cpus = dataaccess.get_all_cpus()
    
    inputlowestfps = determine_cpu_fps_tier(input_cpu, comp_genres)[1]
    
    othercpus = []
    for cpu in all_cpus:
        """ only proceed with CPUs compatible with different chipsets """
        if not cpu.chipset_name: continue
        chipsetsoverlap = len(set(cpu.chipset_name.split(',')).intersection(currchipsets)) > 0
        if chipsetsoverlap: continue
        if determine_cpu_fps_tier(cpu, comp_genres)[0] >= tier: othercpus.append(cpu)
    
    memrecs = generate_memory_config_recommendations(dataaccess.get_all_memory(available=True))
    lowestbytier = {}
    topperforming = None
    lowestdollarfps = None
    for cpu in othercpus:
        if cpu.id == input_cpu.id: continue
        price = lowest_price(cpu.prices)
        if not price: continue
        
        mobos = dataaccess.get_mobos_by_chipset(cpu.chipset_name.split(','), available=True, use_status=BaseComponent.Status.APPROVED)
        cheapestmobo = determine_cheapest_comp(mobos)
        if not cheapestmobo: continue
        
        cpu.recommendedmobo = cheapestmobo
        populate_memory_config(cpu, cheapestmobo, memrecs)
        cheapestmem = cpu.recommendedmemory4gb if cpu.recommendedmemory4gb.price.price < cpu.recommendedmemory8gb.price.price else cpu.recommendedmemory8gb
        
        cpu.price = price
        cpu.platform_price = cpu.price.price + cheapestmem.price.price + cheapestmobo.price.price
        cpu.formattedplatformprice = retaildata_utils.format_int_price(cpu.platform_price)
        cpu.buyurl = price.link
        cpu.formattedprice = price.formatted_price
        
        """ cheapest by tier """
        ptier, lowestfps = determine_cpu_fps_tier(cpu, comp_genres)
        if not ptier or not lowestfps: continue
        if lowestfps < inputlowestfps: continue
        if ptier > tier:
            val = lowestbytier.get(ptier)
            if not val: lowestbytier[ptier] = cpu
            elif cpu.platform_price < val.platform_price: lowestbytier[ptier] = cpu
        
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
        
    
    return lowestbytier, topperforming, lowestdollarfps, memrecs

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
        if not comp: continue
        comptier, complowestfps = determine_cpu_fps_tier(comp, genres)
        if not comptier or not complowestfps: continue
        gains = int(complowestfps - lowestfps)
        comp.fpsgain = gains
        if gains:
            if hasattr(comp, 'platform_price'): comp.dollarfps = comp.platform_price / 100 / gains
            else: comp.dollarfps = comp.price.price / 100 / gains
        else: comp.dollarfps = 'N/A'
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
    
    scs_recs, scs_top, scs_dollarfps = recommend_same_chipset_cpu(input_cpu, input_cpu.chipset_name.split(','), tier, comp_genres)
    np_recs, np_top, np_dollarfps, memrecs = recommend_newplatform_cpu(input_cpu, input_cpu.chipset_name.split(','), tier, comp_genres)
    
    populate_fps_gains(input_cpu, scs_recs.values() + np_recs.values() + [scs_top,scs_dollarfps,np_top,np_dollarfps], comp_genres)
    
    res = {}
    res['scsbytier'] = scs_recs
    res['scstop'] = scs_top
    res['scsbv'] = scs_dollarfps
    res['npbytier'] = np_recs
    res['nptop'] = np_top
    res['npbv'] = np_dollarfps
    res['memrecs'] = memrecs
    
    reccpus = scs_recs.values() + [scs_top] + [scs_dollarfps] + np_recs.values() + [np_top] + [np_dollarfps]
    res['fpsgains'] = performance_gains(input_cpu, reccpus)
    
    return res

def performance_gains(input_cpu, recommended_cpus):
    """
    will return a table for each cpu passed in showing performance data across genres and gains
    {
        "input":{},
        "recs" : {
            657 : {
                "FPS": {
                    "gains" : 5,
                    "dollarfps" : 10
                
                }
            }
        }
    }
    """
    
    retdata = {}
    recs = {}
    retdata['recs'] = recs
    retdata['input'] = input_cpu.fps_data
    
    ifps = {}
    for dp in input_cpu.fps_data: ifps[dp.benchmark_type] = dp.fps_average
    
    for rcpu in recommended_cpus:
        if not rcpu: continue
        for dp in rcpu.fps_data:
            """
            calculate what the fps gain and the dollar per fps is
            """
            infpsaverage = ifps.get(dp.benchmark_type)
            if not infpsaverage: continue
            gains = int(dp.fps_average - infpsaverage)
            if gains < 1: dollarfps = 'N/A'
            else:
                if hasattr(rcpu, 'platform_price'): dollarfps = rcpu.platform_price / 100 / gains
                else: dollarfps = rcpu.price.price / 100 / gains
            
            val = recs.get(rcpu.id)
            if not val: recs[rcpu.id] = {}
            recs[rcpu.id][dp.benchmark_type] = {'gains' : gains, 'dollarfps' : dollarfps}
    
    return retdata
        
    
