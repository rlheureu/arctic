'''
Created on May 15, 2016

@author: shanrandhawa
'''
import datetime

from database import dataaccess
from models.models import User
from utils import auth_utils


def create_user(username, email, password, howheard):
    
    if not username: raise AttributeError('User profile name is a required parameter.')
    if not email: raise AttributeError('Email is a required parameter.')
    if not password: raise AttributeError('Password is a required parameter.')
    
    if not auth_utils.is_valid_email(email):
        raise AttributeError('Invalid email address!')
    
        
    if len(password) < 4:
        raise AttributeError('Invalid email address!')
    
    userexist = dataaccess.get_user_by_email(email)
    if userexist: raise AttributeError('This email is already registered.')
    
    userexist = dataaccess.get_user_by_profilename(username)
    if userexist: raise AttributeError('This profile name already exists.')
        
    user = User()
    user.email = email
    user.password = auth_utils.to_hash(password)
    user.how_hear = howheard
    user.profile_name = username
    user.created_at = datetime.datetime.now()
    
    dataaccess.create_user(user)
    return user
