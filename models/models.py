'''
core_model.py

Core model types defined here
'''
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey, Column
from sqlalchemy.sql.sqltypes import Integer, String, Boolean, Text, DateTime,\
    Float


Base = declarative_base()

class BaseComponent(Base):
    __tablename__ = 'arctic_component'

    id = Column('arctic_component_id', Integer, primary_key=True)
    vendor = Column('vendor_name', String(500))
    brand_name = Column('brand_name', String(500))
    model_number = Column('model_number', String(500))
    max_performance = Column('max_performance', String(500))
    active = Column('active', Boolean)
    display_name = Column('display_name', String(500))
    
    memory_spec = Column('memory_spec', String(500))
    memory_frequency = Column('memory_frequency', String(500))
    socket = Column('socket', String(500))
    unlocked = Column('unlocked', Boolean)
    
    recommended = Column('recommended', Boolean)
    
    sort_order = Column('sort_order', Integer)
    msrp = Column('msrp', Float)
    
    type = Column('data_type_discriminator', String(45))

    __mapper_args__ = {
        'polymorphic_on':type,
        'polymorphic_identity':'base'
    }
    
    def get_type_str(self):
        raise NotImplemented('should be implemented in subclass')
    
    def adjusted_display_name(self):
        if self.display_name: return self.display_name
        part_name = ''
        if self.vendor: part_name += self.vendor + ' '
        if self.brand_name: part_name += self.brand_name + ' '
        if self.model_number: part_name += self.model_number
        return part_name
    
    def get_performance_color(self):
        
        if not self.max_performance or self.max_performance == '':
            """
            performance not available
            """
            return 'gray'
    
        perf = self.max_performance.lower() 
        
        if '4k' in perf:
            return 'purple'
        elif 'vr' in perf:
            return 'black'
        elif '1440p' in perf:
            return 'orange'
        elif '1080p@60' in perf:
            return 'blue'
        elif '1080p@30' in perf:
            return 'green'
        elif '720p' in perf:
            return 'gray'
        else:
            return 'gray'
    
    def get_rgb_colors(self):
        color = self.get_performance_color()
        if color == 'purple':
            return {'r' : 254, 'g' : 74, 'b' : 234}
        elif color == 'black':
            return {'r' : 96, 'g' : 96, 'b' : 96}
        elif color == 'orange':
            return {'r' : 254, 'g' : 222, 'b' : 134}
        elif color == 'blue':
            return {'r' : 41, 'g' : 160, 'b' : 222}
        elif color == 'blue':
            return {'r' : 30, 'g' : 211, 'b' : 17}
        else:
            return {'r' : 51, 'g' : 51, 'b' : 51}
    
    def get_performance_color_coded(self):
        if not self.max_performance or self.max_performance == '':
            """
            performance not available
            """
            return 0
    
        perf = self.max_performance.lower() 
        
        if '4k' in perf:
            return 6
        elif 'vr' in perf:
            return 5
        elif '1440p' in perf:
            return 4
        elif '1080p@60' in perf:
            return 3
        elif '1080p@30' in perf:
            return 2
        elif '720p' in perf:
            return 1
        else:
            return 0

class CPUComponent(BaseComponent):
    
    generation = Column('generation', String(500))
    int_gpu = Column('int_gpu', String(500))
    ####socket = Column('socket', String(500))
    ddr3 = Column('ddr3', String(500))
    ddr3l = Column('ddr3l', String(500))
    ddr4 = Column('ddr4', String(500))
    max_memory_size = Column('max_memory_size', String(500))
    ####unlocked = Column('unlocked', Boolean)
    dx12_cap = Column('dx12_cap', Boolean)
    display_port = Column('display_port', Boolean)
    hdmi = Column('hdmi', Boolean)
    dvi = Column('dvi', Boolean)
    vga = Column('vga', Boolean)
    
    def get_type_str(self):
        return 'Processor'
    
    __mapper_args__ = {
        'polymorphic_identity' : 'CPU'
    }

class GPUComponent(BaseComponent):
    
    def get_type_str(self):
        return 'Graphics'
    
    __mapper_args__ = {
        'polymorphic_identity' : 'GPU'
    }

class ChassisComponent(BaseComponent):
    
    __mapper_args__ = {
        'polymorphic_identity' : 'CHASSIS'
    }
    
    def get_type_str(self):
        return 'Chassis'

class StorageComponent(BaseComponent):
    
    __mapper_args__ = {
        'polymorphic_identity' : 'STORAGE'
    }
    
    def get_type_str(self):
        return 'Storage'

class PowerComponent(BaseComponent):
    
    __mapper_args__ = {
        'polymorphic_identity' : 'POWER'
    }
    
    def get_type_str(self):
        return 'Power Supply'

class MemoryComponent(BaseComponent):
    
    memory_capacity = Column('memory_capacity', String(500))
    memory_config = Column('memory_config', String(500))
    ####memory_spec = Column('memory_spec', String(500))
    ####memory_frequency = Column('memory_frequency', String(500))
    color = Column('color', String(500))
    
    __mapper_args__ = {
        'polymorphic_identity' : 'MEMORY'
    }
    
    def get_type_str(self):
        return 'Memory'
    
class MotherboardComponent(BaseComponent):
    
    chipset_vendor = Column('chipset_vendor', String(500))
    chipset_name = Column('chipset_name', String(500))
    ####memory_spec = Column('memory_spec', String(500))
    ####memory_frequency = Column('memory_frequency', String(500))
    ####socket = Column('socket', String(500))
    form_factor = Column('form_factor', String(500))
    memory_type = Column('memory_type', String(500))
    external_ports = Column('external_ports', String(500))
    pcie_bus = Column('pcie_bus', String(500))
    mpcie = Column('mpcie', String(500))
    ####unlocked = Column('unlocked', Boolean)
    
    __mapper_args__ = {
        'polymorphic_identity' : 'MOTHERBOARD'
    }
    
    def get_type_str(self):
        return 'Motherboard'

class DisplayComponent(BaseComponent):
    
    size = Column('size', String(500))
    resolution = Column('resolution', String(500))
    max_framerate = Column('max_framerate', String(500))
    
    __mapper_args__ = {
        'polymorphic_identity' : 'DISPLAY'
    }
    
    def get_type_str(self):
        return 'Display'

class User(Base, UserMixin):
    __tablename__ = 'arctic_user'

    id = Column('arctic_user_id', Integer, primary_key=True)
    email = Column('email', String(255), unique=True)
    password = Column('password', String(255))
    active = Column('active', Boolean())
    created_at = Column('created_at', DateTime())
    confirmed_at = Column('confirmed_at', DateTime())
    fb_id = Column('fb_id', String(100))
    profile_name = Column('profile_name', String(100))
    how_hear = Column('how_hear', String(1000))
    first_name = Column('first_name', String(100))
    last_name = Column('last_name', String(100))
    fb_token = Column('fb_token', Text)
    superadmin = Column('superadmin', Boolean())

    def __init__(self):
        self.authenticated = False
        self.active = False
        self.anonymous = False
    
    def get_unequipped_parts(self):
        unequipped = []
        for p in self.owned_parts:
            if not p.rig_id:
                unequipped.append(p) 
        return unequipped
    
    def get_id(self): return self.id
    
    def is_super_admin(self):
        return self.superadmin
    def is_authenticated(self): return False
    def is_active(self): return True
    def is_anonymous(self): return False

class Rig(Base):
    __tablename__ = 'arctic_rig'

    id = Column('arctic_rig_id', Integer, primary_key=True)
    name = Column('name', String(400))
    use = Column('use', String(128))
    cpu_component_id = Column('cpu_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    cpu_component = relationship('CPUComponent', foreign_keys='Rig.cpu_component_id')
    gpu_component_id = Column('gpu_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    gpu_component = relationship('GPUComponent', foreign_keys='Rig.gpu_component_id')
    memory_component_id = Column('memory_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    memory_component = relationship('MemoryComponent', foreign_keys='Rig.memory_component_id')
    motherboard_component_id = Column('motherboard_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    motherboard_component = relationship('MotherboardComponent', foreign_keys='Rig.motherboard_component_id')
    display_component_id = Column('display_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    display_component = relationship('DisplayComponent', foreign_keys='Rig.display_component_id')
    power_component_id = Column('power_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    power_component = relationship('PowerComponent', foreign_keys='Rig.power_component_id')
    storage_component_id = Column('storage_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    storage_component = relationship('StorageComponent', foreign_keys='Rig.storage_component_id')
    chassis_component_id = Column('chassis_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    chassis_component = relationship('ChassisComponent', foreign_keys='Rig.chassis_component_id')
    user_id = Column('user_id', Integer, ForeignKey('arctic_user.arctic_user_id'))
    user = relationship('User', foreign_keys='Rig.user_id', backref='rigs')
    rig_preset = Column('rig_preset', Boolean)
    rig_preset_name = Column('rig_preset_name', String(400))
    rig_preset_sort_order = Column('rig_preset_sort_order', Integer)
    rig_preset_description = Column('rig_preset_description', String(1000))
    upgrade_from_id = Column('upgrade_from_id', Integer, ForeignKey('arctic_rig.arctic_rig_id'))
    upgrade_from = relationship('Rig', remote_side=[id])
    
    def get_max_performance_color(self):
        perf_color = self.cpu_component.get_performance_color()
        perf_color_coded = self.cpu_component.get_performance_color_coded()
        max_performance = self.cpu_component.max_performance if self.cpu_component else None
        if self.gpu_component and self.gpu_component.get_performance_color_coded() < perf_color_coded:
            """ GPU has lower performance """
            perf_color = self.gpu_component.get_performance_color()
            perf_color_coded = self.gpu_component.get_performance_color_coded()
            max_performance = self.gpu_component.max_performance
        if self.memory_component and self.memory_component.get_performance_color_coded() < perf_color_coded:
            perf_color = self.memory_component.get_performance_color()
            perf_color_coded = self.memory_component.get_performance_color_coded()
            max_performance = self.memory_component.max_performance
        if self.display_component and self.display_component.get_performance_color_coded() < perf_color_coded:
            perf_color = self.display_component.get_performance_color()
            perf_color_coded = self.display_component.get_performance_color_coded()
            max_performance = self.display_component.max_performance
        
        return perf_color

class OwnedPart(Base):
    __tablename__ = 'arctic_owned_part'

    id = Column('arctic_owned_part_id', Integer, primary_key=True)
    component_id = Column('component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    component = relationship('BaseComponent', foreign_keys='OwnedPart.component_id')
    rig_id = Column('rig_id', Integer, ForeignKey('arctic_rig.arctic_rig_id'))
    rig = relationship('Rig', foreign_keys='OwnedPart.rig_id', backref='owned_parts')
    user_id = Column('user_id', Integer, ForeignKey('arctic_user.arctic_user_id'))
    user = relationship('User', foreign_keys='OwnedPart.user_id', backref='owned_parts')

class ComponentFps(Base):
    __tablename__ = 'arctic_component_fps'

    id = Column('arctic_component_fps_id', Integer, primary_key=True)
    component_id = Column('component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    component = relationship('BaseComponent', foreign_keys='ComponentFps.component_id')
    benchmark_type = Column('benchmark_type', String(128))
    benchmark_name = Column('benchmark_name', String(128))
    description = Column('description', String(512))
    fps_average = Column('fps_average', Float)
    fps_one = Column('fps_one', Float)
    fps_point_one = Column('fps_point_one', Float)
    
class AccountClaim(Base):
    __tablename__ = 'arctic_account_claim'

    id = Column('arctic_account_claim_id', Integer, primary_key=True)
    token = Column('token', String(100))
    user_id = Column('user_id', Integer, ForeignKey('arctic_user.arctic_user_id'))
    user = relationship('User', foreign_keys='AccountClaim.user_id')
    created = Column('created', DateTime)
    expiration = Column('expiration', DateTime)
    claimed = Column('claimed', Boolean)
    account_claim_type = Column('account_claim_type', String(45))
    