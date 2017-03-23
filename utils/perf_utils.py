"""

Performance Utility


"""

def get_fps_map(fps_data):
    
    """
    want to return data in the following format:
    {
        "datapoints":[
            { "price" : 355, "name" : "Display name" , "fps_average" : .. , "component_id" : 123 ...
    }
    """
    max_x = 0
    min_x = None
    max_y = 0
    min_y = None
    alldata = {}
    for fd in fps_data:
        bmarkdata = alldata.get(fd.benchmark_type)
        if not bmarkdata: 
            bmarkdata = {"datapoints" : []}
            alldata[fd.benchmark_type] = bmarkdata
        
        rgbcolors = fd.component.get_rgb_colors()
        bmarkdata['datapoints'].append({
                                        "component_id" : fd.component_id,
                                        "component_display_name" : fd.component.adjusted_display_name(),
                                        "msrp" : fd.component.msrp,
                                        "fps_average" : fd.fps_average,
                                        "fps_one" : fd.fps_one,
                                        "fps_point_one" : fd.fps_point_one,
                                        "svg_plot" : get_svg_data_point(fd),
                                        "benchmark_name" : fd.benchmark_name,
                                        "background_rgba" : "rgba({}, {}, {}, 0.5)".format(rgbcolors['r'], rgbcolors['g'], rgbcolors['b']),
                                        "outline_rgb" : "rgb({}, {}, {})".format(rgbcolors['r'], rgbcolors['g'], rgbcolors['b']),
                                        "perf_color" : fd.component.get_performance_color()
                                        })
        
        if fd.component.msrp > max_x: max_x = fd.component.msrp
        if not min_x or fd.component.msrp < min_x: min_x = fd.component.msrp
        if fd.fps_average > max_y: max_y = fd.fps_average
        if not min_y or fd.fps_point_one < min_y: min_y = fd.fps_point_one
        
    alldata['x_range'] = [min_x, max_x]
    alldata['y_range'] = [min_y, max_y]
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
    
    
        