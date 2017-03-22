'''
mirage_utils.py

Miscellaneous utils
'''
from sqlalchemy.ext.declarative import DeclarativeMeta
import json
import inspect
from datetime import datetime
from pytz import timezone
import subprocess
import os
from sqlalchemy.sql.sqltypes import Float
from decimal import Decimal

def enum(**enums):
    return type('Enum', (), enums)

def jsonify_sql_alchemy_model(revisit_self=False, fields_to_expand=[]):
    _visited_objs = []
    class SqlAlchemyModelEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj.__class__, DeclarativeMeta):
                # don't re-visit self
                if revisit_self:
                    if obj in _visited_objs:
                        return None
                    _visited_objs.append(obj)

                # go through each field in this SQLalchemy class
                fields = {}
                for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                    val = obj.__getattribute__(field)

                    if not hasattr(val, '__class__'):
                        continue

                    # is this field another SQLalchemy object, or a list of SQLalchemy objects?
                    if isinstance(val.__class__, DeclarativeMeta) or (isinstance(val, list) and len(val) > 0 and isinstance(val[0].__class__, DeclarativeMeta)):
                        # unless we're expanding this field, stop here
                        if field not in fields_to_expand:
                            # not expanding this field: set it to None and continue
                            fields[field] = None
                            continue
                    elif isinstance(val, datetime):
                        val = val.strftime('%m/%d/%Y')
                    elif isinstance(val, Decimal):
                        val = str(val)
                    elif inspect.ismethod(val):
                        continue

                    fields[field] = val
                # a json-encodable dict
                return fields

            return json.JSONEncoder.default(self, obj)
    return SqlAlchemyModelEncoder

def ensure_dictobjs_have_ids(id_key_name='id', dictobj=None, dictobjs=None):
    """
    checks that all objects have IDs
    """
    if dictobj:
        dictobjs = []
        dictobjs.append(dictobj)

    if dictobjs:
        for dictob in dictobjs:
            if not dictob.get(id_key_name):
                return False
    return True

def extract_dictobjs_keyvals(dictobjs=None, dictobj=None, key_name='id', force=False):
    """
    will extract values for a specified key from a list of dict objs
    if force is set to true it will return a list of any keyvals found. if force
    is false it will return an empty list if any key is missing
    """
    if dictobj:
        dictobjs = []
        dictobjs.append(dictobj)

    rv = []

    if dictobjs:
        for dictob in dictobjs:
            val = dictob.get(key_name)
            if not val:
                return []
            else:
                rv.append(val)

    return rv

def db_objs_list_to_map_by_id(db_objs):
    """
    maps a list of db objects by there ids
    """

    objmap = {}
    for db_ob in db_objs:
        objmap[db_ob.id] = db_ob
    return objmap

def dictobjslist_to_mapbykey(key_name='id', dictobjs=None, force=False):
    """
    will map object by specified key_name
    if force is set to True it will return a list of any objects found with the key. if force
    is False it will return None if the key is missing from any object
    """

    rv = {}

    if dictobjs:
        for dictob in dictobjs:
            val = dictob.get(key_name)
            if not val and not force:
                return None
            else:
                rv[val] = dictob


    return rv

def construct_paginated_bar(current_page, total_pages):
    page_elements = []

    if current_page != 1 and not total_pages <= 5 and not current_page < (total_pages - (total_pages - 4)):
        page_elements.append(PaginatedElement(current_page=False, display_value='&laquo;', page_value=str(1)))
        page_elements.append(PaginatedElement(current_page=False, display_value='&lsaquo;', page_value=str(current_page - 1)))

    if total_pages <= 5:
        # create simple paginated bar
        for i in range(0, total_pages):
            page_elements.append(PaginatedElement(current_page=((i + 1) == current_page), display_value=str(i + 1), page_value=str(i + 1)))
    else:
        # create paginated bar with placeholders
        page_counter = 1

        if current_page > 2:
            page_counter = current_page - 2
        else:
            page_counter = 1;
        # now, if the start page is close to the end
        if current_page > (total_pages - 2):
            # we are close to the last page
            page_counter = total_pages - 4;
        for i in range(0, 5):
            page_elements.append(PaginatedElement(current_page=(page_counter == current_page), display_value=page_counter, page_value=str(page_counter)));
            page_counter += 1

        if current_page != total_pages and not current_page > (total_pages - 3) and total_pages > 1:
            page_elements.append(PaginatedElement(current_page=False, display_value='&rsaquo;', page_value=str(current_page + 1)));
            page_elements.append(PaginatedElement(current_page=False, display_value='&raquo;', page_value=str(total_pages)));

    return page_elements

class PaginatedElement():
    def __init__(self, current_page=None, display_value=None, page_value=None):
        self.current_page = current_page
        self.display_value = display_value
        self.page_value = page_value

def local_time(datetime, fmt='%m/%d/%Y %H:%M'):
    datetime_aware = datetime.replace(tzinfo=timezone('UTC'))
    '''TODO: see if this can be stored in the session. Defaulting to US/Pacific for now.'''
    local_tz = timezone('US/Pacific')
    local_datetime = datetime_aware.astimezone(local_tz)
    return local_datetime.strftime(fmt)
