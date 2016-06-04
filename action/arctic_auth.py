'''
Created on May 15, 2016

@author: shanrandhawa
'''

from utils import auth_utils

from database import dataaccess

def authenticate(email,password):
    
    if not email or not password:
        raise AttributeError('Email and password are required arguments!')
    
    if not auth_utils.is_valid_email(email):
        raise AttributeError('Invalid Email Address!')
    
    user = dataaccess.get_user_by_email(email)
    
    if user and auth_utils.verify(user.password, password):
        return user
    else:
        return None

def load_user_by_id(userid):
    return dataaccess.get_user_by_id(userid)
