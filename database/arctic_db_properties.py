'''
Created on Jul 6, 2017

@author: shanrandhawa
'''
from database import db
from models import models


def get_property(property_name):
    prop = db.session().query(models.ArcticProperties).filter(models.ArcticProperties.property_name == property_name).first()
    if prop: return prop.property_value
    else: return None