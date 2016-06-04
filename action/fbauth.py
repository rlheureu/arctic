'''
Created on May 8, 2016

@author: shanrandhawa
'''
import json
import os

import requests

from database.database import db
from models import models
from flask_login import login_user




def is_fb_user_registered(fb_userid):
    """
    retrieves user from database by facebook ID
    """
    return fetch_user_by_fbid(fb_userid) != None

def fetch_user_by_fbid(fb_id):
    return db.session().query(models.User).filter(models.User.fb_id == fb_id).first()

def registernew(fb_userid, fbtoken, profilename, howhearabout):
    """
    creates new user after validation. returns newly created user
    """
    if not profilenameavailable(profilename): raise ValueError('Profile name not available')
    if is_fb_user_registered(fb_userid): raise ValueError('This facebook user already exists')
    if not is_user_fb_authenticated(fbtoken): raise ValueError('Not logged into FB')
    
    user = models.User()
    user.profile_name = profilename
    user.fb_id = fb_userid
    user.how_hear = howhearabout
    db.session().add(user)
    db.session().commit()
    return user
    
def profilenameavailable(profilename):
    user = db.session().query(models.User).filter(models.User.profile_name == profilename).first()
    return user == None

def set_session_valid(user):
    user.authenticated = True
    user.active = True
    user.anonymous = False

def load_valid_user_session(fbid):
    user = fetch_user_by_fbid(fbid)
    if not user: return None
    if not user.fb_token: return user
    if is_user_fb_authenticated(user.fb_token): return set_session_valid(user)

def login_fb_user(fb_id, fb_token):
    """
    this method will create the server side (database) Arctic session for the user
    it will ensure that the user is currently logged into FB and AC.
    """
    user = fetch_user_by_fbid(fb_id)
    if not user: raise ValueError('User does not exist')
    if not is_user_fb_authenticated(fb_token): raise ValueError('User not authenticated with FB.')
    
    """ that should do it, store the token and create the user object """
    user.fb_token = fb_token
    db.session().add(user)
    db.session().commit()
    
    set_session_valid(user)
    login_user(user)
    

def is_user_logged_in(userid):
    """
    takes passed in user id and checks to see if the session is valid
    it will not check against facebook every time - only if the session was
    last checked more than x minutes ago
    """
    pass

def logout_user(userid):
    """
    logs out user from AC and FB
    this can be called from client if the fb
    client lib determines the user has logged out of FB.
    """
    pass

def is_user_fb_authenticated(token):
    """
    will make server call to facebook to ensure that the user token is
    valid i.e. will verify that the user is logged into facebook and amdahl cube
    """
    accesstoken = get_fb_app_access_token() #### <----- NEED TO CACHE THIS!!
    
    r = requests.get('https://graph.facebook.com/debug_token?input_token={}&access_token={}'
                 .format(token, accesstoken))
    
    if r.status_code == 200:
        response = json.loads(r.text)
        return response.get('data').get('is_valid')
    else:
        return False

def get_fb_app_access_token():
    """
    TODO!!!!!
    
    THIS CALL DOES NOT NEED TO MADE EVERY TIME!!!!!!!!
    """
    
    url = 'https://graph.facebook.com/oauth/access_token?client_id={}&client_secret={}&grant_type=client_credentials'
    formatted = url.format(os.environ.get('FB_CLIENT_ID'), os.environ.get('FB_CLIENT_SECRET'))
    
    print formatted
    
    r = requests.get(formatted)
    print r.status_code
    print r.text
    
    if r.status_code == 200:
        return r.text[r.text.find('access_token=')+len('access_token='):]
    else:
        return None
