'''
Created on May 15, 2016

@author: shanrandhawa
'''

from passlib.apps import custom_app_context as pwd_context
import re

def to_hash(cleartext):
    return pwd_context.encrypt(cleartext)

def verify(hashed, cleartext):
    return pwd_context.verify(cleartext, hashed)

def is_valid_email(email):
    return False if not re.match(r"[^@]+@[^@]+\.[^@]+", email) else True
