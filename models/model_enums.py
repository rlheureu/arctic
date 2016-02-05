'''
Define States
'''

class Component:
    GPU = 'GPU'
    CPU = 'CPU'
    MOTHERBOARD = 'MOTHERBOARD'
    MEMORY = 'MEMORY'
    DISPLAY = 'DISPLAY'

def get_enum_values(obj):
    """
    Returns list of values of enum attributes. Determines enum attribute by looking for attributes that do not start with '_'
    """
    vals = []
    for field in [x for x in dir(obj) if not x.startswith('_')]:
        vals.append(getattr(obj, field))
    return vals
