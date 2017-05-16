'''
Created on May 10, 2017

@author: shanrandhawa
'''
import re


def sticks_and_capacity(title):
    """
    Returns a tuple of the number of: number of memory sticks, capacity of each stick
    """
    
    title = title.lower()
    nstitle = "".join(title.split())
    
    match = re.match(r".*(\d+)x(\d+)g", nstitle)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    match = re.match(r".*(\d+)gb{0,1}x(\d+)", nstitle)
    if match:
        return int(match.group(2)), int(match.group(1))
    
    """ assuming only one stick """
    match = re.match(r".*(\d+)\s{0,1}gb\s+", title)
    if match:
        return 1, int(match.group(1))
    return None

def memory_frequency(title):
    """
    Will return memory frequency for MHz only.
    Example input: "Something 1600 MHz" returns 1600
    """
    
    title = title.lower()
    m = re.match(r'.*\s(\d+)\s{0,1}mhz', title)
    if m: return int(m.group(1))
    return None
    
def memtype(title):
    """
    Returns type of memory based on input string.
    Only will return DDR3 or DDR4 if found surrounded by whitespace in input string.
    """
    
    title = title.lower()
    if re.match(r'.*\s(ddr3)\s', title): return 'DDR3'
    if re.match(r'.*\s(ddr4)\s', title): return 'DDR4'
    return None

def format_int_price(intval):
    """
    takes a price (e.g. $54.97 as an int of 5497 and returns the formatted string)
    """
    intstr = str(intval)
    
    if len(intstr) == 1: return '$0.0{}'.format(intstr)
    if len(intstr) == 2: return '$0.{}'.format(intstr)
    
    dollars = intstr[:len(intstr)-2]
    cents = intstr[len(intstr)-2:]
    
    rem = len(dollars) % 3 if len(dollars) > 3 else None
    if rem:
        toformat = dollars[rem:]
        mid = ','.join([toformat[i:i+3] for i in range(0, len(toformat), 3)])
        return "${},{}.{}".format(dollars[:rem], mid, cents)
    else:
        dollars = ','.join([dollars[i:i+3] for i in range(0, len(dollars), 3)])
        return "${}.{}".format(dollars, cents)
    
    
    
    