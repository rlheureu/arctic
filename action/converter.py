'''
converter.py

template for handling conversions from dictionary objects to entities.
'''
from datetime import datetime
import json
import logging

from models.model_enums import OrderStates, TestStates
from models.models import Sample, Order, Test, Assay, SampleType, Category, Target, Method, SampleQuantityType, User, OrderComment, TestComment, OrderFilter, TestFilter, \
    SubCategory, AssayComment, CustomerAccount, ReportSignature, Asset, \
    OrderAttachment, TestAttachment, AssayAttachment, CustomerComment, \
    CustomerAttachment, DefaultComment
from utils.gen_utils import jsonify_sql_alchemy_model


logger = logging.getLogger('app')

class EntConverter:

    def __init__(self, dict_obj, db_obj=None):

        self._dict_obj = dict_obj
        self._db_obj = db_obj


    def _get_entity(self):

        if self._db_obj:
            return self._db_obj
        else:
            return self._new_entity()

    def _new_entity(self):
        raise 'Must be implemented in subclass.'

    def get(self):

        ent = self._get_entity()

        for k in self._dict_obj:
            if k == 'id':
                continue
            if hasattr(ent, k):
                if self._dict_obj.get(k) == 'None' or self._dict_obj.get(k) == '':
                    setattr(ent, k, None)
                elif ('_date' in k or 'date_' in k) and self._dict_obj.get(k) != None:
                    setattr(ent, k, datetime.strptime(self._dict_obj.get(k), "%m/%d/%Y"))
                else:
                    setattr(ent, k, self._dict_obj.get(k))
            else:
                continue

        if hasattr(ent, 'state') and ent.state == None:
            ent.state = self._set_initial_state()

        if ent.id == None:
            ent.date_created = datetime.today()

        logger.info('Dict converted to entity, JSON repr: ' + json.dumps(ent, cls=jsonify_sql_alchemy_model(False, []), check_circular=False))

        return ent

class SampleConverter(EntConverter):

    def _new_entity(self):

        return Sample()

class OrderConverter(EntConverter):

    def _new_entity(self):

        return Order()

    def _set_initial_state(self):

        return OrderStates.CREATED

class TestConverter(EntConverter):

    def _new_entity(self):

        return Test()

    def _set_initial_state(self):

        return TestStates.NOT_STARTED

class AssayConverter(EntConverter):

    def _new_entity(self):

        return Assay()

class SampleTypeConverter(EntConverter):

    def _new_entity(self):

        return SampleType()

class CategoryConverter(EntConverter):

    def _new_entity(self):

        return Category()

class SubCategoryConverter(EntConverter):

    def _new_entity(self):

        return SubCategory()

class TargetConverter(EntConverter):

    def _new_entity(self):

        return Target()

class MethodConverter(EntConverter):

    def _new_entity(self):

        return Method()

class SampleQuantityTypeConverter(EntConverter):

    def _new_entity(self):

        return SampleQuantityType()

class DefaultCommentConverter(EntConverter):

    def _new_entity(self):

        return DefaultComment()

class UserConverter(EntConverter):

    def _new_entity(self):

        return User()

class OrderCommentConverter(EntConverter):

    def _new_entity(self):

        return OrderComment()

class TestCommentConverter(EntConverter):

    def _new_entity(self):

        return TestComment()

class AssayCommentConverter(EntConverter):

    def _new_entity(self):

        return AssayComment()

class CustomerCommentConverter(EntConverter):

    def _new_entity(self):

        return CustomerComment()

class OrderFilterConverter(EntConverter):

    def _new_entity(self):

        return OrderFilter()

class TestFilterConverter(EntConverter):

    def _new_entity(self):

        return TestFilter()

class CustomerAccountConverter(EntConverter):

    def _new_entity(self):

        return CustomerAccount()

class ReportSignatureConverter(EntConverter):

    def _new_entity(self):

        return ReportSignature()

class AssetConverter(EntConverter):

    def _new_entity(self):

        return Asset()

class OrderAttachmentConverter(EntConverter):

    def _new_entity(self):

        return OrderAttachment()

class TestAttachmentConverter(EntConverter):

    def _new_entity(self):

        return TestAttachment()

class AssayAttachmentConverter(EntConverter):

    def _new_entity(self):

        return AssayAttachment()

class CustomerAttachmentConverter(EntConverter):

    def _new_entity(self):

        return CustomerAttachment()
