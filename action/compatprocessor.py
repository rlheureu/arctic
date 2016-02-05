'''
Created on Jan 21, 2016

@author: shanrandhawa
'''
from models.model_enums import Component

class BaseCompatProcessor():
    
    def generate_query(self, current_rig):
        """
        soooo I guess this should not call the database?
        """
        
        """
        how will this check then?
        
        can it build the query? NO... no DB logic should be here
        
        can it build the query using a query builder object?? ... yessss perhapss
        
        """
        
        self._process()
        
        pass
    
    def _process(self):
        raise NotImplementedError('Implement in subclass')


class CPUCompatProcessor(BaseCompatProcessor):
    pass

class GPUCompatProcessor(BaseCompatProcessor):
    pass

class MemoryCompatProcessor(BaseCompatProcessor):
    pass

class DisplayCompatProcessor(BaseCompatProcessor):
    pass

class MotherboardCompatProcessor(BaseCompatProcessor):
    pass
    

compat_registry = {Component.CPU : CPUCompatProcessor,
                   Component.GPU : GPUCompatProcessor,
                   Component.DISPLAY : DisplayCompatProcessor,
                   Component.MEMORY : MemoryCompatProcessor,
                   Component.MOTHERBOARD : MotherboardCompatProcessor}

def get_compat_processor(component_type):
    return compat_registry.get(component_type)()