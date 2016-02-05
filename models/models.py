'''
core_model.py

Core model types defined here
'''
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey, Column
from sqlalchemy.sql.sqltypes import Integer, String, Boolean


Base = declarative_base()



class BaseComponent(Base):
    __tablename__ = 'arctic_component'

    id = Column('arctic_component_id', Integer, primary_key=True)
    vendor = Column('vendor_name', String(500))
    brand_name = Column('brand_name', String(500))
    model_number = Column('model_number', String(500))
    max_performance = Column('max_performance', String(500))
    active = Column('active', Boolean)
    
    memory_spec = Column('memory_spec', String(500))
    memory_frequency = Column('memory_frequency', String(500))
    socket = Column('socket', String(500))
    unlocked = Column('unlocked', Boolean)
    
    
    type = Column('data_type_discriminator', String(45))

    __mapper_args__ = {
        'polymorphic_on':type,
        'polymorphic_identity':'base'
    }

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
    
    __mapper_args__ = {
        'polymorphic_identity' : 'CPU'
    }

class MemoryComponent(BaseComponent):
    
    memory_capacity = Column('memory_capacity', String(500))
    memory_config = Column('memory_config', String(500))
    ####memory_spec = Column('memory_spec', String(500))
    ####memory_frequency = Column('memory_frequency', String(500))
    color = Column('color', String(500))
    
    __mapper_args__ = {
        'polymorphic_identity' : 'MEMORY'
    }
    
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

class DisplayComponent(BaseComponent):
    
    size = Column('size', String(500))
    resolution = Column('resolution', String(500))
    max_framerate = Column('max_framerate', String(500))
    
    __mapper_args__ = {
        'polymorphic_identity' : 'DISPLAY'
    }

class User(Base):
    __tablename__ = 'arctic_user'

    id = Column('arctic_user_id', Integer, primary_key=True)
    first_name = Column('first_name', String(100))
    last_name = Column('last_name', String(100))

class Rig(Base):
    __tablename__ = 'arctic_rig'

    id = Column('arctic_rig_id', Integer, primary_key=True)
    name = Column('name', String(500))
    cpu_component_id = Column('cpu_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    cpu_component = relationship('CPUComponent', foreign_keys='Rig.cpu_component_id')
    memory_component_id = Column('memory_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    memory_component = relationship('MemoryComponent', foreign_keys='Rig.memory_component_id')
    motherboard_component_id = Column('motherboard_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    motherboard_component = relationship('MotherboardComponent', foreign_keys='Rig.motherboard_component_id')
    display_component_id = Column('display_component_id', Integer, ForeignKey('arctic_component.arctic_component_id'))
    display_component = relationship('DisplayComponent', foreign_keys='Rig.display_component_id')
    user_id = Column('user_id', Integer, ForeignKey('arctic_user.arctic_user_id'))
    user = relationship('User', foreign_keys='Rig.user_id')
    