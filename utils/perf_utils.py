"""

Performance Utility


"""

def set_performance_color_for_parts(components):
    for c in components:
        c.perf_color = get_performance_color(c)
        c.perf_color_coded = get_performance_color_coded(c)

def get_performance_color(component):
    
    if not component.max_performance or component.max_performance == '':
        """
        performance not available
        """
        return 'gray'
    
    perf = component.max_performance.lower() 
    
    if '4k' in perf:
        return 'purple'
    elif '1440p' in perf:
        return 'orange'
    elif 'oculus' in perf:
        return 'black'
    elif '1080p' in perf:
        return 'blue'
    elif '720p' in perf:
        return 'white'
    else:
        return 'gray'
    
def get_performance_color_coded(component):
    
    if not component.max_performance or component.max_performance == '':
        """
        performance not available
        """
        return 0
    
    perf = component.max_performance.lower() 
    
    if '4k' in perf:
        return 5
    elif '1440p' in perf:
        return 4
    elif 'oculus' in perf:
        return 3
    elif '1080p' in perf:
        return 2
    elif '720p' in perf:
        return 1
    else:
        return 0
        