"""

Performance Utility


"""

def to_datapoint_json(fd):
    rgbcolors = fd.component.get_rgb_colors()
    return {
        "component_id" : fd.component_id,
        "component_display_name" : fd.component.adjusted_display_name(),
        "msrp" : fd.component.msrp,
        "fps_average" : fd.fps_average,
        "fps_one" : fd.fps_one,
        "fps_point_one" : fd.fps_point_one,
        "svg_plot" : get_svg_data_point(fd),
        "benchmark_name" : fd.benchmark_name,
        "source_url" : fd.source_url,
        "source_description" : fd.source_description,
        "background_rgba" : "rgba({}, {}, {}, 0.5)".format(rgbcolors['r'], rgbcolors['g'], rgbcolors['b']),
        "outline_rgb" : "rgb({}, {}, {})".format(rgbcolors['r'], rgbcolors['g'], rgbcolors['b']),
        "perf_color" : fd.component.get_performance_color()
    }

def get_fps_map(fps_data):
    
    """
    want to return data in the following format:
    {
        "datapoints":[
            { "price" : 355, "name" : "Display name" , "fps_average" : .. , "component_id" : 123 ...
    }
    """
    alldata = {}
    
    groupedfps = group_overlapping_by_bracket(fps_data)
    
    for bmarktype in groupedfps.keys():
        
        bmarkdata = alldata.get(bmarktype)
        
        if not bmarkdata: 
            bmarkdata = {"datapoints" : []}
            alldata[bmarktype] = bmarkdata
        
        for fpsgroup in groupedfps.get(bmarktype):
        
            fd = fpsgroup['top']
            
            
            
            datapointinfo = to_datapoint_json(fd)
            datapointinfo['others'] = []
            
            for otherfd in fpsgroup['others']:
                datapointinfo['others'].append(to_datapoint_json(otherfd))
            
            bmarkdata['datapoints'].append(datapointinfo)
    
    return alldata
        
def get_svg_data_point(fd):
    
    """
    Example:  'M 1 1 L 1 2 L 0.5 3 L 1.5 3 L 1 2 Z',
    """
    
    msrp = fd.component.msrp
    fps_avg = fd.fps_average
    fps_one = fd.fps_one
    fps_point_one = fd.fps_point_one
    
    if msrp == None or fps_avg == None or fps_one == None or fps_point_one == None: return None
    
    return "M {} {} L {} {} L {} {} L {} {} L {} {} Z".format(msrp,
                                                              fps_point_one,
                                                              msrp,
                                                              fps_one,
                                                              float(msrp) - 3,
                                                              fps_avg,
                                                              float(msrp) + 3,
                                                              fps_avg,
                                                              msrp,
                                                              fps_one)
def get_rectangle(fps_datapoint):
    return {'x1': fps_datapoint.component.msrp - 3,
            'x2': fps_datapoint.component.msrp + 3,
            'y1': fps_datapoint.fps_point_one,
            'y2': fps_datapoint.fps_average}

def group_overlapping_by_bracket(fps_data):
    """
    this method will group components that are within a $10 range
    i.e. $0-$10, $11-$20, etc.
    """
    allgroups = {}
    for fpDp in fps_data:
        
        groups = allgroups.get(fpDp.benchmark_type)
        if not groups:
            groups = {}
            allgroups[fpDp.benchmark_type] = groups
        if not fpDp.component.msrp: continue
        
        group_bracket = int(fpDp.component.msrp)/10
        
        group = groups.get(group_bracket)
        if not group:
            groups[group_bracket] = {'top' : fpDp, 'others' : []}
            continue
        else:
            currtop = group['top']
            if currtop.fps_average > fpDp.fps_average: group['others'].append(fpDp)
            else:
                group['others'].append(group['top'])
                group['top'] = currtop
    
    """ convert to list for backwards compatibility """
    for btype in allgroups.keys():
        groupsmap = allgroups.get(btype)
        
        allgroups[btype] = groupsmap.values()
    
    return allgroups

def group_overlapping_legacy(fps_data):
    
    allgroups = {}
    for fpDp in fps_data:
        
        groups = allgroups.get(fpDp.benchmark_type)
        if not groups:
            groups = []
            allgroups[fpDp.benchmark_type] = groups
        if not fpDp.component.msrp: continue
        
        rect = get_rectangle(fpDp)
        
        overlapping_groups = []
        
        for group in groups:
            if is_overlapping(rect, group['rect']):
                
                overlapping_groups.append(group)
                if len(overlapping_groups) > 1:
                    """ ONLY ADD TO ONE GROUP, consolidate later """
                    continue
                
                """ combine the two and update """
                group['rect'] = combine_rects(rect, group['rect'])
                
                """ add datapoint to group as top or remainder """
                top_rect = get_rectangle(group['top'])
                if top_rect['y2'] > rect['y2']: group['others'].append(fpDp)
                else:
                    """ this is new top performer, move prev to others list """
                    group['others'].append(group['top'])
                    group['top'] = fpDp
        
        if not len(overlapping_groups):
            """ no overlapping found, add rect as its own group """
            groups.append({'rect' : rect, 'others': [], 'top': fpDp})
            
        elif len(overlapping_groups) > 1:
            """ the component matched with multiple groups - need to consolidate """
            primary_group = overlapping_groups[0]
            for idx, group in enumerate(overlapping_groups):
                if idx == 0: continue
                
                primary_group['rect'] = combine_rects(primary_group['rect'], group['rect'])
                top_rect_p = get_rectangle(primary_group['top'])
                top_rect_g = get_rectangle(group['top'])
                if top_rect_p['y2'] > top_rect_g['y2']:
                    primary_group['others'].append(group['top'])
                else:
                    """ the top rect of other group is higher than top of primary """
                    primary_group['others'].append(primary_group['top'])
                    primary_group['top'] = group['top']
                for group_other in group['others']:
                    primary_group['others'].append(group_other)
                
                """ remove this group from list of groups """
                groups.remove(group)
    
    return allgroups

def is_overlapping(recta, rectb):
    """
    recta and rectb are rectangles on a cartesian plane, each with fields x1,x2,y1,y2
    x1<x2, y1<y2
    rectangle:
        x1,y2------------x2,y2
        |                    |
        |                    |
        x1,y1------------x2,y1
    
    this function will return true if the rectangles overlap. they are considered overlapping even if their lines overlap
    """
    
    if (recta['y2'] < rectb['y1']) or (rectb['y2'] < recta['y1']): return False
    if (recta['x2'] < rectb['x1']) or (rectb['x2'] < recta['x1']) : return False
    return True
    
def combine_rects(recta, rectb):
    """
    will return a large rectangle comprise of the two
    """
    return  {
            'x1':min(recta['x1'], rectb['x1']),
            'x2':max(recta['x2'], rectb['x2']),
            'y1':min(recta['y1'], rectb['y1']),
            'y2':max(recta['y2'], rectb['y2'])
            }
    
def set_performance_color_for_rigs(rigs):
    for rig in rigs:
        rig.perf_color = get_performance_color(rig.cpu_component)
        rig.perf_color_coded = get_performance_color_coded(rig.cpu_component)
        rig.max_performance = rig.cpu_component.max_performance if rig.cpu_component else None
        if rig.gpu_component and get_performance_color_coded(rig.gpu_component) < rig.perf_color_coded:
            rig.perf_color = get_performance_color(rig.gpu_component)
            rig.perf_color_coded = get_performance_color_coded(rig.gpu_component)
            rig.max_performance = rig.gpu_component.max_performance
        if rig.memory_component and get_performance_color_coded(rig.memory_component) < rig.perf_color_coded:
            rig.perf_color = get_performance_color(rig.memory_component)
            rig.perf_color_coded = get_performance_color_coded(rig.memory_component)
            rig.max_performance = rig.memory_component.max_performance
        if rig.display_component and get_performance_color_coded(rig.display_component) < rig.perf_color_coded:
            rig.perf_color = get_performance_color(rig.display_component)
            rig.perf_color_coded = get_performance_color_coded(rig.display_component)
            rig.max_performance = rig.display_component.max_performance
        

def set_performance_color_for_parts(components):
    for c in components:
        c.perf_color = get_performance_color(c)
        c.perf_color_coded = get_performance_color_coded(c)

def get_performance_color(component):
    
    if component: return component.get_performance_color()
    else: return 'gray'
    
def get_performance_color_coded(component):
    
    if component: return component.get_performance_color_coded()
    else: return 0
    
    
        