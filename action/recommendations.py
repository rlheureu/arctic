'''
Created on May 3, 2017

@author: shanrandhawa


recommendations service

'''
from database import dataaccess


class RecInputs:
    pass

class RecResponse:
    pass

def recommend_cpu(recinput):
    pass

def determine_cheapest_comp(comps):
    cheapest = None
    for comp in comps:
        
        if not comp.msrp: continue
        
        if not cheapest: cheapest = comp
        elif comp.msrp < cheapest.msrp: cheapest = comp
        
    return cheapest

def determine_cheapest_mem(mems, capacity_target, dimms=4):
    """
    based on list of memory items passed in will determine the cheapest combination of memory
    """
    
    cheapest = None
    
    for mem in mems:
        
        if not mem.msrp: continue
        
        """ if mem does not meet cap requirement increment until it does """
        qty = 1
        if mem.memory_capacity < capacity_target:
            
            if mem.memory_capacity * dimms < capacity_target:
                """ there are not enough dimms to reach cap target """
                continue
            
            qty = capacity_target/mem.memory_capacity + capacity_target%mem.memory_capacity
            
        mem.platform_price = mem.msrp * qty
        mem.platform_qty = qty
        
        if not cheapest: cheapest = mem
        elif mem.platform_price < cheapest.platform_price: cheapest = mem
    
    return cheapest
        
            
    

def determine_platform_costs(cpus):
    """
    Will determine the platform cost for each of the CPUs passed in and
    return a list of CPUs with the cheapest memory and motherboard populated.
    """
    
    retcpus = []
    
    for cpu in cpus:
        
        if not cpu.msrp or not cpu.available: continue
        
        mobos = dataaccess.get_compatible_mobo_map(cpu_id=cpu.id)
        cheapest_mobo = determine_cheapest_comp(mobos)
        if not cheapest_mobo: continue
        
        mems = dataaccess.get_compatible_memory_map(cpu_id=cpu.id)
        cheapest_mem = determine_cheapest_mem(mems, 4) # note: for now this is 4GB and 4 slots
        if not cheapest_mem: continue
        
        cpu.platform_memory = cheapest_mem
        cpu.platform_mobo = cheapest_mobo
        cpu.platform_total_cost = cpu.msrp + cheapest_mem.msrp + cheapest_mobo.msrp
        
        retcpus.append(cpu)
    
    return retcpus

def lowest_platform_cost(cpus):
    
    popcpus = determine_platform_costs(cpus)
    cheapest = None
    for cpu in popcpus:
        
        if not cheapest: cheapest = cpu
        elif cpu.platform_total_cost < cheapest.platform_total_cost: cheapest = cpu
        
    return cheapest

def determine_cpu_fps_tier(cpu_comp, genres):
    
    bygenre = {}
    
    for datapoint in cpu_comp.fps_data:
        """ we only want to look at the first-person shooter data """
        genre = str(datapoint.benchmark_type)
        
        if datapoint.fps_average >= 144: bygenre[genre] = 6
        elif datapoint.fps_average >= 120: bygenre[genre] = 5 
        elif datapoint.fps_one >= 60: bygenre[genre] = 4
        elif datapoint.fps_average >= 60: bygenre[genre] = 3
        elif datapoint.fps_one >= 30: bygenre[genre] = 2
        elif datapoint.fps_average >= 30: bygenre[genre] = 1
    
    if len(bygenre.values()) == 0: return 0
    
    """ if the same set of genres are not being compared then return 0 (i.e. data is incomplete) """
    print 'comparing comp genres with actual ' + str(genres) + ' actual ' + str(set(bygenre.keys()))
    if len(set(genres).intersection(set(bygenre.keys()))) != len(set(genres)):
        print 'returning 0'
        return 0
    
    return min(bygenre.values())

def get_fps_per_dollar_gains(oldcpu, newcpu, upgrade_cost):
    
    oldfps = None
    newfps = None
    for datapoint in oldcpu.fps_data:
        if str(datapoint.benchmark_name) == 'OPEN_WORLD':
            oldfps = datapoint.fps_average
            break
    for datapoint in newcpu.fps_data:
        if str(datapoint.benchmark_name) == 'OPEN_WORLD':
            newfps = datapoint.fps_average
            break
    
    if not oldfps or not newfps: return 0
    else: return float(newfps - oldfps) / float(upgrade_cost)        

def recommend_a_cpu(input_cpu):
    """
    returns a recommended CPU based on the inputs provided
    """
    
    """ first which tier does this CPU fall into? """
    comp_genres = []
    for dp in input_cpu.fps_data: comp_genres.append(str(dp.benchmark_type))
    tier = determine_cpu_fps_tier(input_cpu, set(comp_genres))
    
    print 'the tier is ' + str(tier)
    
    """ there is no better part to recommend """
    if tier == 6: return None
    
    """
    at this point there can be two different types of recommendations
    - same chipset
    - new platform
    """
    
    """
    --------------
    SAME chipset
    --------------
    """
    same_cs_cpus = dataaccess.get_cpus_by_chipset(input_cpu.chipset_name.split(','))
    
    print 'cps list ' + str(same_cs_cpus)
    
    """ 
    look at the next highest tier to recommend a CPU
    iterate through all CPUs and find a part that is just one tier higher and costs the least amount
    """
    same_chipset_results = {}
    tiercounter = tier + 1
    while True:
        if tiercounter > 6: break
        
        lowest_msrp_same_cs = None
        
        for cpu in same_cs_cpus:
            if not cpu.msrp: continue
            
            if determine_cpu_fps_tier(cpu, set(comp_genres)) == (tiercounter) and (not lowest_msrp_same_cs or cpu.msrp < lowest_msrp_same_cs.msrp):
                lowest_msrp_same_cs = cpu
        
        same_chipset_results[tiercounter] = lowest_msrp_same_cs
        
        tiercounter += 1
    
    
    """
    -------------------
    new platform option
    -------------------
    now we're looking for options that are *not* part of the same chipset (as above)..
    """
    all_cpus = dataaccess.get_all_cpus()
    new_platform_results = {}
    tiercounter = tier + 1
    while True:
        if tiercounter > 6: break
        other_cpus = []
        
        """ filter out chipsets - THERES A BETTER WAY TO DO THIS! """
        for cpu in all_cpus:
            if not cpu.chipset_name or not input_cpu.chipset_name: continue
            
            if len(set(cpu.chipset_name.split(',')).intersection(input_cpu.chipset_name.split(','))) == 0 and determine_cpu_fps_tier(cpu, comp_genres) == tiercounter:
                """ this means this is a new option """
                other_cpus.append(cpu)
        
        new_platform_results[tiercounter] = lowest_platform_cost(other_cpus)
        
        tiercounter += 1
    
    
    """ now recommend the cheapest based on platform price """
    
    
    res = RecResponse()
    res.same_socket_upgrades = same_chipset_results
    res.new_platform_upgrades = new_platform_results
    res.current_tier = tier
    res.input_cpu = input_cpu
    
    return res

