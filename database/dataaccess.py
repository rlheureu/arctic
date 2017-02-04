

from datetime import datetime

from flask_login import current_user
from sqlalchemy.sql.expression import or_

from database import db
from models import models
from models.models import AccountClaim, OwnedPart, CPUComponent, GPUComponent,\
    MemoryComponent, DisplayComponent, MotherboardComponent, ChassisComponent,\
    PowerComponent, StorageComponent
from utils.exception import InvalidInput
import simplejson



def superadmin_save_components(user, savelist):
    """
    superadmin saving of components
    """
    print "savelist is {}".format(savelist)
    ids = savelist.keys()
    
    for cid in ids:
        """ get component """
        
        comp = None
        print "the cid is {}".format(cid)
        if "cpu" in cid.lower(): comp = CPUComponent()
        elif "gpu" in cid.lower(): comp = GPUComponent()
        elif "mem" in cid.lower(): comp = MemoryComponent()
        elif "disp" in cid.lower(): comp = DisplayComponent()
        elif "mother" in cid.lower(): comp = MotherboardComponent()
        elif "chassis" in cid.lower(): comp = ChassisComponent()
        elif "power" in cid.lower(): comp = PowerComponent()
        elif "storage" in cid.lower(): comp = StorageComponent()
        else: comp = db.session().query(models.BaseComponent).filter(models.BaseComponent.id == cid).first()
        
        
        updates = savelist.get(cid)
        fields = updates.keys()
        
        for field in fields:
            setattr(comp, field, updates.get(field))
        
        db.session().add(comp)
    
    db.session().flush()
    

def get_rig_presets():
    return db.session().query(models.Rig).filter(models.Rig.rig_preset == True).order_by(models.Rig.rig_preset_sort_order.desc()).all()

def get_all_cpus(active_only=True):
    q = db.session().query(models.CPUComponent)
    if active_only: q.filter(models.CPUComponent.active == True)
    return q.all()

def get_all_gpus(return_query=False, active_only=True):
    q = db.session().query(models.GPUComponent)
    if active_only: q.filter(models.GPUComponent.active == True)
    if return_query:
        return q
    else:
        return q.all()

def get_all_chassis(return_query=False, active_only=True):
    q = db.session().query(models.ChassisComponent)
    if active_only: q.filter(models.ChassisComponent.active == True)
    if return_query:
        return q
    else:
        return q.all()

def get_all_power(return_query=False, active_only=True):
    q = db.session().query(models.PowerComponent)
    if active_only: q.filter(models.PowerComponent.active == True)
    if return_query:
        return q
    else:
        return q.all()

def get_all_storage(return_query=False, active_only=True):
    q = db.session().query(models.StorageComponent)
    if active_only: q.filter(models.StorageComponent.active == True)
    if return_query:
        return q
    else:
        return q.all()

def get_all_mobos(active_only=True):
    q = db.session().query(models.MotherboardComponent)
    if active_only: q.filter(models.MotherboardComponent.active == True)
    return q.all()

def get_all_displays(return_query=False,active_only=True):
    q = db.session().query(models.DisplayComponent)
    if active_only: q.filter(models.DisplayComponent.active == True)
    if return_query:
        return q
    else:
        return q.all()

def get_all_memory(active_only=True):
    q = db.session().query(models.MemoryComponent)
    if active_only: q.filter(models.MemoryComponent.active == True)
    return q.all()

def get_component(component_id):
    if component_id:
        return db.session().query(models.BaseComponent).filter(models.BaseComponent.id == component_id).filter(models.BaseComponent.active == True).first()
    else:
        return None

def get_rig(rig_id):
    return db.session().query(models.Rig).filter(models.Rig.id == rig_id).first()

def get_part(part_id):
    return db.session().query(models.OwnedPart).filter(models.OwnedPart.id == part_id).first()

def extract_component_ids(rig_dict):
    component_ids = []
    if rig_dict.get('cpu_id'): component_ids.append(int(rig_dict.get('cpu_id')))
    if rig_dict.get('display_id'): component_ids.append(int(rig_dict.get('display_id')))
    if rig_dict.get('memory_id'): component_ids.append(int(rig_dict.get('memory_id')))
    if rig_dict.get('motherboard_id'): component_ids.append(int(rig_dict.get('motherboard_id')))
    if rig_dict.get('gpu_id'): component_ids.append(int(rig_dict.get('gpu_id')))
    if rig_dict.get('power_id'): component_ids.append(int(rig_dict.get('power_id')))
    if rig_dict.get('storage_id'): component_ids.append(int(rig_dict.get('storage_id')))
    if rig_dict.get('chassis_id'): component_ids.append(int(rig_dict.get('chassis_id')))
    return component_ids

def save_rig(rig_dict, user_id):
    
    rig = get_rig(rig_dict.get('rig_id')) if rig_dict.get('rig_id') else models.Rig()
    rig.cpu_component = get_component(rig_dict.get('cpu_id'))
    rig.display_component = get_component(rig_dict.get('display_id'))
    rig.memory_component = get_component(rig_dict.get('memory_id'))
    rig.motherboard_component = get_component(rig_dict.get('motherboard_id'))
    rig.gpu_component = get_component(rig_dict.get('gpu_id'))
    rig.power_component = get_component(rig_dict.get('power_id'))
    rig.storage_component = get_component(rig_dict.get('storage_id'))
    rig.chassis_component = get_component(rig_dict.get('chassis_id'))
    rig.name = rig_dict.get('name')
    if rig_dict.get('owned'): rig.use = 'owned' if rig_dict.get('owned') == 'true' else 'other'
    if not rig.user_id: rig.user_id = user_id
    
    db.session().add(rig)
    db.session().flush()
    
    component_ids = set(extract_component_ids(rig_dict))
    if rig.use == 'owned':
        """ determine the updated parts and add them as owned parts """
        owned_parts_set = set()
        for part in rig.owned_parts:
            owned_parts_set.add(part.component.id)
            
            """ also unequip any existing owned parts that are not in the newest save """
            if not part.component.id in component_ids:
                part.rig_id = None
                db.session().add(part)
        
        """ get all unequipped parts """
        user = get_user_by_id(user_id)
        unequipped_parts_dict = {}
        for part in user.owned_parts:
            if part.rig_id == None:
                unequipped_parts_dict[part.component_id] = part
        
        for component_id in component_ids:
            if not component_id in owned_parts_set:
                """ this part needs to be either created or found and equipped """
                
                op = None
                if unequipped_parts_dict.get(component_id):
                    op = unequipped_parts_dict.get(component_id)
                else:
                    op = OwnedPart()
                    op.component_id = component_id
                    op.user_id = user_id
                
                op.rig_id = rig.id
                db.session().add(op)
                
    else:
        """ if there are equipped owned parts, unequip them """
        for part in rig.owned_parts:
            part.rig_id = None
            db.session().add(part)
    
    db.session().flush()
    
    return rig

def modify_use(rig_dict, user_id):
    
    if not rig_dict.get('rig_id'): return None
    rig = get_rig(rig_dict.get('rig_id'))
    if rig.user_id != user_id: return None

    rig.use = rig_dict.get('use')
        
    db.session().add(rig)
    db.session().flush()
    
    return rig

def remove_part(part_id, user_id):
    
    part = get_part(part_id)
    if part.user_id != user_id: return None
        
    db.session().delete(part)
    db.session().flush()
    
    return part_id

def delete_rig(rig_id):
    
    rig = get_rig(rig_id)
    if not rig:
        raise InvalidInput('This rig does not exists cannot delete')
    
    if current_user.id != rig.user.id:
        raise InvalidInput('You can only delete your own rig!')
    
    db.session().delete(rig)
    db.session().flush()
    

def get_manufacturers(target):

    if target == 'cpu':
        query = db.session().query(models.CPUComponent.vendor.distinct().label("vendor"))
        manufacturers = [row.vendor for row in query.all() if row.vendor]
    elif target == 'display':
        query = db.session().query(models.DisplayComponent.vendor.distinct().label("vendor"))
        manufacturers = [row.vendor for row in query.all() if row.vendor]
    elif target == 'memory':
        query = db.session().query(models.MemoryComponent.vendor.distinct().label("vendor"))
        manufacturers = [row.vendor for row in query.all() if row.vendor]
    elif target == 'gpu':
        query = db.session().query(models.GPUComponent.vendor.distinct().label("vendor"))
        manufacturers = [row.vendor for row in query.all() if row.vendor]
    elif target == 'motherboard':
        query = db.session().query(models.MotherboardComponent.vendor.distinct().label("vendor"))
        manufacturers = [row.vendor for row in query.all() if row.vendor]
    elif target == 'chassis':
        query = db.session().query(models.ChassisComponent.vendor.distinct().label("vendor"))
        manufacturers = [row.vendor for row in query.all() if row.vendor]
    elif target == 'power':
        query = db.session().query(models.PowerComponent.vendor.distinct().label("vendor"))
        manufacturers = [row.vendor for row in query.all() if row.vendor]
    elif target == 'storage':
        query = db.session().query(models.StorageComponent.vendor.distinct().label("vendor"))
        manufacturers = [row.vendor for row in query.all() if row.vendor]
    else:
        manufacturers = []

    manufacturers.sort()
    return manufacturers

def search_parts(search_string, target, motherboard_id=None, gpu_id=None, memory_id=None, display_id=None, cpu_id=None, manufacturer=None):
    print manufacturer
    search_strings = search_string.split()

    if target == 'cpu':
        query = get_compatible_cpu_map(motherboard_id, gpu_id, memory_id, display_id, cpu_id, return_query=True)
        if manufacturer:
            query = query.filter(models.CPUComponent.vendor == manufacturer)
        for search_string in search_strings:
            query = query.filter(or_(models.CPUComponent.vendor.like('%' + search_string + '%'),
                                     models.CPUComponent.brand_name.like('%' + search_string + '%'),
                                     models.CPUComponent.model_number.like('%' + search_string + '%'),
                                     models.CPUComponent.display_name.like('%' + search_string + '%'),
                                     models.CPUComponent.int_gpu.like('%' + search_string + '%')))
        return query.all()

    elif target == 'display':
        query = get_all_displays(return_query=True)
        if manufacturer:
            query = query.filter(models.DisplayComponent.vendor == manufacturer)
        for search_string in search_strings:
            query = query.filter(or_(models.DisplayComponent.vendor.like('%' + search_string + '%'),
                                     models.DisplayComponent.brand_name.like('%' + search_string + '%'),
                                     models.DisplayComponent.model_number.like('%' + search_string + '%'),
                                     models.DisplayComponent.display_name.like('%' + search_string + '%')))
        return query.all()

    elif target == 'memory':
        query = get_compatible_memory_map(motherboard_id, gpu_id, memory_id, display_id, cpu_id, return_query=True)
        if manufacturer:
            query = query.filter(models.MemoryComponent.vendor == manufacturer)
        for search_string in search_strings:
            query = query.filter(or_(models.MemoryComponent.vendor.like('%' + search_string + '%'),
                                     models.MemoryComponent.brand_name.like('%' + search_string + '%'),
                                     models.MemoryComponent.model_number.like('%' + search_string + '%'),
                                     models.MemoryComponent.display_name.like('%' + search_string + '%')))
        return query.all()

    elif target == 'gpu':
        query = get_all_gpus(return_query=True)
        if manufacturer:
            query = query.filter(models.GPUComponent.vendor == manufacturer)
        for search_string in search_strings:
            query = query.filter(or_(models.GPUComponent.vendor.like('%' + search_string + '%'),
                                     models.GPUComponent.brand_name.like('%' + search_string + '%'),
                                     models.GPUComponent.model_number.like('%' + search_string + '%'),
                                     models.GPUComponent.display_name.like('%' + search_string + '%')))
        return query.all()

    elif target == 'motherboard':
        query = get_compatible_mobo_map(motherboard_id, gpu_id, memory_id, display_id, cpu_id, return_query=True)
        if manufacturer:
            query = query.filter(models.MotherboardComponent.vendor == manufacturer)
        for search_string in search_strings:
            query = query.filter(or_(models.MotherboardComponent.vendor.like('%' + search_string + '%'),
                                     models.MotherboardComponent.brand_name.like('%' + search_string + '%'),
                                     models.MotherboardComponent.model_number.like('%' + search_string + '%'),
                                     models.MotherboardComponent.display_name.like('%' + search_string + '%'),
                                     models.MotherboardComponent.chipset_vendor.like('%' + search_string + '%'),
                                     models.MotherboardComponent.chipset_name.like('%' + search_string + '%'),
                                     models.MotherboardComponent.form_factor.like('%' + search_string + '%'),
                                     models.MotherboardComponent.memory_type.like('%' + search_string + '%')))
        return query.all()

    elif target == 'chassis':
        query = get_all_chassis(return_query=True)
        if manufacturer:
            query = query.filter(models.ChassisComponent.vendor == manufacturer)
        for search_string in search_strings:
            query = query.filter(or_(models.ChassisComponent.vendor.like('%' + search_string + '%'),
                                     models.ChassisComponent.brand_name.like('%' + search_string + '%'),
                                     models.ChassisComponent.model_number.like('%' + search_string + '%'),
                                     models.ChassisComponent.display_name.like('%' + search_string + '%')))
        return query.all()

    elif target == 'power':
        query = get_all_power(return_query=True)
        if manufacturer:
            query = query.filter(models.PowerComponent.vendor == manufacturer)
        for search_string in search_strings:
            query = query.filter(or_(models.PowerComponent.vendor.like('%' + search_string + '%'),
                                     models.PowerComponent.brand_name.like('%' + search_string + '%'),
                                     models.PowerComponent.model_number.like('%' + search_string + '%'),
                                     models.PowerComponent.display_name.like('%' + search_string + '%')))
        return query.all()

    elif target == 'storage':
        query = get_all_storage(return_query=True)
        if manufacturer:
            query = query.filter(models.StorageComponent.vendor == manufacturer)
        for search_string in search_strings:
            query = query.filter(or_(models.StorageComponent.vendor.like('%' + search_string + '%'),
                                     models.StorageComponent.brand_name.like('%' + search_string + '%'),
                                     models.StorageComponent.model_number.like('%' + search_string + '%'),
                                     models.StorageComponent.display_name.like('%' + search_string + '%')))
        return query.all()

    else:
        return []

def get_compatible_parts(target=None,
                         motherboard_id=None,
                         gpu_id=None,
                         memory_id=None,
                         display_id=None,
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
    elif target == 'motherboard':
        """
        check processor and memory
        """
        return get_compatible_mobo_map(motherboard_id, gpu_id, memory_id, display_id, cpu_id)
    elif target == 'chassis':
        return get_all_chassis()
    elif target == 'power':
        return get_all_power()
    elif target == 'storage':
        return get_all_storage()
    else:
        return []

def get_compatible_mobo_map(motherboard_id=None, gpu_id=None, memory_id=None, display_id=None, cpu_id=None, return_query=False):
    """
    MOBO constraints:
    - CPU YES
    - Memory YES
    """
    
    compat_q = None
    
    if cpu_id:
        print 'cpu ID: {}'.format(cpu_id)
        cpu = db.session().query(models.CPUComponent).filter(models.CPUComponent.id == cpu_id, models.CPUComponent.active == True).first()
        print 'cpu: {}'.format(cpu)
        """ socket compare """
        compat_q = db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.socket == cpu.socket, models.MotherboardComponent.active == True)
        
    elif memory_id:
        mem = db.session().query(models.MemoryComponent).filter(models.MemoryComponent.id == memory_id, models.MemoryComponent.active == True).first()
        
        """ get compatible sockets from compatible cpus """
        allcpus = db.session().query(models.CPUComponent).filter(models.CPUComponent.active == True).all()
        compatsockets = set()
        for cpu in allcpus:
            if mem.memory_spec == 'ddr3' and cpu.ddr3 != None and cpu.ddr3 != '' and cpu.ddr3.lower() != 'no':
                compatsockets.add(cpu.socket)
            elif mem.memory_spec == 'ddr3l' and cpu.ddr3l != None and cpu.ddr3l != '' and cpu.ddr3l.lower() != 'no':
                compatsockets.add(cpu.socket)
            elif mem.memory_spec == 'ddr4' and cpu.ddr4 != None and cpu.ddr4 != '' and cpu.ddr4.lower() != 'no':
                compatsockets.add(cpu.socket)
        
        print 'compat sockets {}'.format(compatsockets)
        compat_q = db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.socket.in_(compatsockets), models.MotherboardComponent.active == True)
    
    """
    return map of compatible and incompatible components
    """
    if compat_q:
        if return_query:
            return compat_q
        else:
            return compat_q.all()
    else:
        if return_query:
            return db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.active == True)
        else:
            return db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.active == True).all()
    
def get_compatible_memory_map(motherboard_id=None, gpu_id=None, memory_id=None, display_id=None, cpu_id=None, return_query=False):
    """
    Memory constraints:
    - CPU
    """
    
    compat_q = None
    
    if cpu_id:
        """
        which memory is supported for selected CPU?
        """
        cpu = db.session().query(models.CPUComponent).filter(models.CPUComponent.id == cpu_id, models.CPUComponent.active == True).first()
        
        print 'cpu mem [{}]'.format(cpu.ddr3)
        print 'cpu mem [{}]'.format(cpu.ddr3l)
        print 'cpu mem [{}]'.format(cpu.ddr4)
        
        supported_mem = []
        if cpu.ddr3 != None and cpu.ddr3 != '' and cpu.ddr3.lower() != 'no' : supported_mem.append('ddr3')
        if cpu.ddr3l != None and cpu.ddr3l != '' and cpu.ddr3l.lower() != 'no' : supported_mem.append('ddr3l')
        if cpu.ddr4 != None and cpu.ddr4 != '' and cpu.ddr4.lower() != 'no' : supported_mem.append('ddr4')
        
        print supported_mem
        
        compat_q = db.session().query(models.MemoryComponent).filter(models.MemoryComponent.memory_spec.in_(supported_mem), models.MemoryComponent.active == True)
    
    """
    return map of compatible and incompatible components
    """
    if compat_q:
        if return_query:
            return compat_q
        else:
            return compat_q.all()
    else:
        if return_query:
            return db.session().query(models.MemoryComponent).filter(models.MemoryComponent.active == True)
        else:
            return db.session().query(models.MemoryComponent).filter(models.MemoryComponent.active == True).all()

def get_compatible_cpu_map(motherboard_id=None, gpu_id=None, memory_id=None, display_id=None, cpu_id=None, return_query=False):
    """
    CPU constraints:
    - Motherboard
    - Memory
    """
    
    compat_q = None
    
    if motherboard_id and memory_id:
        mem = db.session().query(models.MemoryComponent).filter(models.MemoryComponent.id == memory_id, models.MemoryComponent.active == True).first()
        mobo = db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.id == motherboard_id, models.MotherboardComponent.active == True).first()
        
        compat_q = get_compat_cpu_for_memspec_queries(mem.memory_spec).filter(models.CPUComponent.socket == mobo.socket)
        
    elif motherboard_id:
        mobo = db.session().query(models.MotherboardComponent).filter(models.MotherboardComponent.id == motherboard_id, models.MotherboardComponent.active == True).first()
        compat_q = db.session().query(models.CPUComponent).filter(models.CPUComponent.socket == mobo.socket, models.CPUComponent.active == True)
    elif memory_id:
        """
        Limit motherboards by mem
        """
        mem = db.session().query(models.MemoryComponent).filter(models.MemoryComponent.id == memory_id, models.MemoryComponent.active == True).first()
        compat_q = get_compat_cpu_for_memspec_queries(mem.memory_spec)
    
    
    """
    return map of compatible and incompatible components
    """
    if compat_q:
        if return_query:
            return compat_q
        else:
            return compat_q.all()
    else:
        if return_query:
            return db.session().query(models.CPUComponent).filter(models.CPUComponent.active == True)
        else:
            return db.session().query(models.CPUComponent).filter(models.CPUComponent.active == True).all()

def get_compat_cpu_for_memspec_queries(memspec):
    """
    Returns queries for compatible and incompatible
    """
    memspec = memspec.lower()
    
    compat = None
    if memspec == 'ddr4':
        compat = db.session().query(models.CPUComponent).filter(models.CPUComponent.ddr4 != 'No') \
        .filter(models.CPUComponent.ddr4 != '') \
        .filter(models.CPUComponent.ddr4 != None) \
        .filter(models.CPUComponent.active == True)
        
    elif memspec == 'ddr3':
        compat = db.session().query(models.CPUComponent).filter(models.CPUComponent.ddr3 != 'No') \
        .filter(models.CPUComponent.ddr3 != '') \
        .filter(models.CPUComponent.ddr3 != None) \
        .filter(models.CPUComponent.active == True)
    elif memspec == 'ddr3l':
        compat = db.session().query(models.CPUComponent).filter(models.CPUComponent.ddr3l != 'No') \
        .filter(models.CPUComponent.ddr3l != '') \
        .filter(models.CPUComponent.ddr3l != None) \
        .filter(models.CPUComponent.active == True)
    return compat

def get_user_by_email(email):
    return db.session().query(models.User).filter(models.User.email == email).first()

def get_user_by_profilename(pname):
    return db.session().query(models.User).filter(models.User.profile_name == pname).first()

def get_user_by_id(userid):
    return db.session().query(models.User).filter(models.User.id == userid).first()

def get_rigs_by_user_id(user_id):
    return db.session().query(models.Rig).filter(models.Rig.user_id == user_id).all()

def create_user(user):
    db.session().add(user)
    db.session().commit()

def save_user(user):
    db.session().add(user)
    db.session().commit()
