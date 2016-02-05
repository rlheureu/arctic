'''
base_service.py

Generic business logic for working with multiple DB models
'''
import json
from database.database import db
from utils import gen_utils
import logging
from models.models import Test
from datetime import datetime

logger = logging.getLogger('app')

class BaseMirageService(object):

    def create_entity_from_dict(self, dict_obj):

        logger.info('Create request incoming, DICT: ' + json.dumps(dict_obj))

        entity = self._converter(dict_obj).get()

        if entity:
            db.session().add(entity)
            db.session().commit()

            self.after_create(entity)

            return entity.id

        return None

    def after_create(self, entity):
        pass

    def update_entity_from_dict(self, dict_obj):

        logger.info('Update request incoming, DICT: ' + json.dumps(dict_obj))

        if not gen_utils.ensure_dictobjs_have_ids(dictobj=dict_obj):
            '''
            TODO probably need to raise an exception here
            '''
            raise ValueError('Dictionary objects must contain an "id" field in order to perform an update.')

        ent = self.retrieve_entity_by_id(gen_utils.extract_dictobjs_keyvals(dictobj=dict_obj))

        entity = self._converter(dict_obj, db_obj=ent).get()

        db.session().add(entity)
        db.session().commit()

        self.after_create(entity)

    def create_entities_from_dict_list(self, dict_objs):

        logger.info('Create request for list incoming, DICT: ' + json.dumps(dict_objs))

        entities = []

        for dict_obj in dict_objs:
            entity = self._converter(dict_obj).get()
            entities.append(entity)

        if len(entities) > 0:
            db.session().add_all(entities)
            db.session().commit()

            created_ids = []
            for entity in entities:
                created_ids.append(entity.id)
                self.after_create(entity)

            return created_ids

        return None

    def update_entities_from_dict_list(self, dict_objs):

        if not gen_utils.ensure_dictobjs_have_ids(dictobjs=dict_objs):
            '''
            TODO probably need to raise an exception here
            '''
            raise ValueError('Dictionary objects must contain an "id" field in order to perform an update.')

        ents = self.retrieve_entities_by_ids(gen_utils.extract_dictobjs_keyvals(dictobjs=dict_objs))
        ent_map = gen_utils.db_objs_list_to_map_by_id(ents)

        entities = []

        for dict_obj in dict_objs:
            ent = self._converter(dict_obj, db_obj=ent_map.get(int(dict_obj.get('id')))).get()
            entities.append(ent)

        db.session().add_all(entities)
        db.session().commit()

        for entity in entities:
            self.after_create(entity)

    def save_entity_to_db(self, entity):
        db.session().add(entity)
        db.session().commit()

        self.after_create(entity)

    def delete_entity_by_id(self, entity_id):
        entity = db.session().query(self._type).filter_by(id=entity_id).first()
        db.session().delete(entity)
        db.session().commit()

    def mark_entity_deleted_by_id(self, entity_id):
        if not hasattr(self._type, 'deleted'):
            raise AttributeError('Entity type passed in does have a "deleted" attribute.')
        entity = self.retrieve_entity_by_id(entity_id)
        entity.deleted = True
        db.session().add(entity)
        db.session().commit()

        self.after_create(entity)

    def mark_entities_deleted_by_ids(self, entity_ids):
        if not hasattr(self._type, 'deleted'):
            raise AttributeError('Entity type passed in does have a "deleted" attribute.')
        entities = self.retrieve_entities_by_ids(entity_ids)
        for entity in entities:
            entity.deleted = True
        db.session().add_all(entities)
        db.session().commit()

        for entity in entities:
            self.after_create(entity)

    def retrieve_entity_by_id(self, entity_id):
        return db.session().query(self._type).filter_by(id=entity_id).first()

    def retrieve_entities_by_ids(self, entity_ids):
        return db.session().query(self._type).filter(self._type.id.in_(entity_ids)).all()

    def retrieve_all_entities(self, join=None, order_by_field=None):
        if join:
            return db.session().query(self._type).join(join).order_by(order_by_field).all()
        else:
            return db.session().query(self._type).order_by(order_by_field).all()

    def _get_page_count(self, total_count, page_size):
        page_count = None
        if total_count > page_size and total_count % page_size != 0:
            page_count = (total_count / page_size) + 1
        else:
            page_count = total_count / page_size
        return page_count

    def append_test_query_with_refine_view_params(self, query, assay_ids, tech_ids, start_date):
        if assay_ids:
            query = query.filter(Test.assay_id.in_(assay_ids))
        if tech_ids:
            query = query.filter(Test.tech_id.in_(tech_ids))
        if start_date:
            query = query.filter(Test.start_date == datetime.strptime(start_date, '%m/%d/%Y'))
        return query

class PaginatedResult():
    def __init__(self):
        self.page_number = None
        self.total_pages = None
        self.results = None

class PagingLinksResult():
    def __init__(self, position=None, total_count=None, previous_id=None, next_id=None):
        self.position = position
        self.total_count = total_count
        self.previous_id = previous_id
        self.next_id = next_id

class RefineViewParams():
    def __init__(self, assays=None, techs=None):
        self.assays = assays
        self.techs = techs
