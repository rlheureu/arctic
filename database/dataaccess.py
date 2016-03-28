

from database import db
from models import models

def get_all_cpus():
    return db.session().query(models.CPUComponent).all()

def get_all_gpus():
    return db.session().query(models.GPUComponent).all()

def get_all_mobos():
    return db.session().query(models.MotherboardComponent).all()

def get_all_displays():
    return db.session().query(models.DisplayComponent).all()

def get_all_memory():
    return db.session().query(models.MemoryComponent).all()

def get_component(component_id):
    if component_id:
        return db.session().query(models.BaseComponent).filter(models.BaseComponent.id == component_id).first()
    else:
        return None

def get_rig(rig_id):
    return db.session().query(models.Rig).filter(models.Rig.id == rig_id).first()

def save_rig(rig_dict, user_id):
    
    rig = get_rig(rig_dict.get('rig_id')) if rig_dict.get('rig_id') else models.Rig()
    rig.cpu_component = get_component(rig_dict.get('cpu_component_id'))
    rig.display_component = get_component(rig_dict.get('display_component_id'))
    rig.memory_component = get_component(rig_dict.get('memory_component_id'))
    rig.motherboard_component = get_component(rig_dict.get('motherboard_component_id'))
    rig.user_id = user_id
    
    db.session().add(rig)
    db.session().flush()
    
    return rig

def get_compatible_parts(target=None,
                         motherboard_id = None,
                         gpu_id = None,
                         memory_id = None,
                         display_id = None,
                         cpu_id=None):
    
    if target == 'cpu':
        return get_compatible_cpu_map(motherboard_id, gpu_id, memory_id, display_id, cpu_id)
    elif target == 'display':
        """
        TODO should we check dvi vga etc.?
        """
        return get_all_displays()
    elif target == 'memory':
        """
        need to check processor (motherboard?)
        """
        return get_compatible_memory_map(motherboard_id, gpu_id, memory_id, display_id, cpu_id)
    elif target == 'gpu':
        """
        check anything? 
        """
        return get_all_gpus()
    elif target == 'mobo':
        """
        check processor and memory
        """
        return get_compatible_mobo_map(motherboard_id, gpu_id, memory_id, display_id, cpu_id)
    
    pass

def get_compatible_mobo_map(motherboard_id = None, gpu_id = None, memory_id = None, display_id = None, cpu_id=None):
    """
    MOBO constraints:
    - CPU YES
    - Memory YES
    """
    
    compat_q = None
    
    if cpu_id:
        print 'cpu ID: {}'.format(cpu_id)
        cpu = db.session().query(models.CPUComponent).filter(models.CPUComponent.id == cpu_id).first()
        print 'cpu: {}'.format(cpu)
        """ socket compare """
        compat_q = db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.socket == cpu.socket)
        
    elif memory_id:
        mem = db.session().query(models.MemoryComponent).filter(models.MemoryComponent.id == memory_id).first()
        
        """ get compatible sockets from compatible cpus """
        allcpus = db.session().query(models.CPUComponent).all()
        compatsockets = set()
        for cpu in allcpus:
            if mem.memory_spec == 'ddr3' and cpu.ddr3 != None and cpu.ddr3 != '' and cpu.ddr3.lower() != 'no':
                compatsockets.add(cpu.socket)
            elif mem.memory_spec == 'ddr3l' and cpu.ddr3l != None and cpu.ddr3l != '' and cpu.ddr3l.lower() != 'no':
                compatsockets.add(cpu.socket)
            elif mem.memory_spec == 'ddr4' and cpu.ddr4 != None and cpu.ddr4 != '' and cpu.ddr4.lower() != 'no':
                compatsockets.add(cpu.socket)
        
        print 'compat sockets {}'.format(compatsockets)
        compat_q = db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.socket.in_(compatsockets))
    
    """
    return map of compatible and incompatible components
    """
    if compat_q:
        return compat_q.all()
    else:
        return db.session().query(models.MotherboardComponent).all()
    
def get_compatible_memory_map(motherboard_id = None, gpu_id = None, memory_id = None, display_id = None, cpu_id=None):
    """
    Memory constraints:
    - CPU
    """
    
    compat_q = None
    
    if cpu_id:
        """
        which memory is supported for selected CPU?
        """
        cpu = db.session().query(models.CPUComponent).filter(models.CPUComponent.id == cpu_id).first()
        
        print 'cpu mem [{}]'.format(cpu.ddr3)
        print 'cpu mem [{}]'.format(cpu.ddr3l)
        print 'cpu mem [{}]'.format(cpu.ddr4)
        
        supported_mem = []
        if cpu.ddr3 != None and cpu.ddr3 != '' and cpu.ddr3.lower() != 'no' : supported_mem.append('ddr3')
        if cpu.ddr3l != None and cpu.ddr3l != '' and cpu.ddr3l.lower() != 'no' : supported_mem.append('ddr3l')
        if cpu.ddr4 != None and cpu.ddr4 != '' and cpu.ddr4.lower() != 'no' : supported_mem.append('ddr4')
        
        print supported_mem
        
        compat_q = db.session().query(models.MemoryComponent).filter(models.MemoryComponent.memory_spec.in_(supported_mem))
    
    """
    return map of compatible and incompatible components
    """
    if compat_q:
        return compat_q.all()
    else:
        return db.session().query(models.MemoryComponent).all()

def get_compatible_cpu_map(motherboard_id = None, gpu_id = None, memory_id = None, display_id = None, cpu_id=None):
    """
    CPU constraints:
    - Motherboard
    - Memory
    """
    
    compat_q = None
    
    if motherboard_id and memory_id:
        mem = db.session().query(models.MemoryComponent).filter(models.MemoryComponent.id == memory_id).first()
        mobo = db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.id == motherboard_id).first()
        
        mem_compat_q = get_compat_cpu_for_memspec_queries(mem.memory_spec)
        mobo_compat_q = db.session().query(models.CPUComponent).filter(models.CPUComponent.socket == mobo.socket)
        
        compat_q = mem_compat_q.intersect(mobo_compat_q)
        
    elif motherboard_id:
        mobo = db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.id == motherboard_id).first()
        compat_q = db.session().query(models.CPUComponent).filter(models.CPUComponent.socket == mobo.socket)
    elif memory_id:
        """
        Limit motherboards by mem
        """
        mem = db.session().query(models.MemoryComponent).filter(models.MemoryComponent.id == memory_id).first()
        compat_q = get_compat_cpu_for_memspec_queries(mem.memory_spec)
    
    
    """
    return map of compatible and incompatible components
    """
    all_cpu = db.session().query(models.CPUComponent)
    if compat_q:
        return compat_q.all()
    else:
        return all_cpu.all()

def get_compat_cpu_for_memspec_queries(memspec):
    """
    Returns queries for compatible and incompatible
    """
    compat = None
    if memspec == 'ddr4':
        compat = db.session().query(models.CPUComponent).filter(models.CPUComponent.ddr4 != 'NO' and
                                                                    models.CPUComponent.ddr4 != '' and
                                                                    models.CPUComponent.ddr4 != None)
    elif memspec == 'ddr3':
        compat = db.session().query(models.CPUComponent).filter(models.CPUComponent.ddr3 != 'NO' and
                                                                    models.CPUComponent.ddr3 != '' and
                                                                    models.CPUComponent.ddr3 != None)
    elif memspec == 'ddr3l':
        compat = db.session().query(models.CPUComponent).filter(models.CPUComponent.ddr3l != 'NO' and
                                                                    models.CPUComponent.ddr3l != '' and
                                                                    models.CPUComponent.ddr3l != None)
    return compat