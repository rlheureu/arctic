'''
Created on May 31, 2017

@author: shanrandhawa
'''


def get_score_available_and_recommended(part):
    if hasattr(part, "compatible") and not part.compatible: return -1
    if part.recommended and part.available: return 2 + int(part.sort_order) if part.sort_order else 2
    elif part.available and len(part.prices) > 0: return 1
    else: return 0 

def sort_by_available_and_recommended(a,b):
    """
    unavailable parts receive the lowest score
    parts that are recommended and available receive the highest score
    """
    return get_score_available_and_recommended(a) - get_score_available_and_recommended(b)
