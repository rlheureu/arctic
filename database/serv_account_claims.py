'''
Created on Aug 14, 2016

@author: shanrandhawa
'''

import datetime
import logging
import uuid



from database import db
from models.models import AccountClaim
from utils.exception import ClaimExistsException


LOG = logging.getLogger('app')

class AccountClaimTypes:
    FORGOT_PASSWORD = 'FORGOT_PASSWORD'

class AccountClaimService():

    def is_claim_valid(self, claim):
        current_time = datetime.datetime.utcnow()
        if current_time > claim.expiration or claim.claimed:
            return False
        else:
            return True

    def retrieve_claim(self, token):
        """
        will retrieve claim if exists (does not do any validity checking!!!)
        """
        return db.session().query(AccountClaim).filter(AccountClaim.token == token).first()

    def retrieve_claim_by_user_id_claim_type(self, user_id, claim_type):

        return db.session().query(AccountClaim).filter(AccountClaim.user_id == user_id,
                                                       AccountClaim.account_claim_type == claim_type).first()

    def mark_claimed(self, claim):
        claim.claimed = True
        db.session().add(claim)
        db.session().flush()

    def create_claim_for_user(self, user, claimtype, expiration_hours):
        """
        Creates a new claim if a similar claim does not already exists.
        Returns the newly created claim.
        """

        LOG.info('Creating claim {} for user {}'.format(claimtype, user.email))

        """
        ensure there are no similar existing claims within timeframe
        """
        current_time = datetime.datetime.utcnow()
        expires = current_time - datetime.timedelta(hours=expiration_hours)
        claims = db.session().query(AccountClaim) \
        .filter(AccountClaim.user == user) \
        .filter(AccountClaim.account_claim_type == claimtype) \
        .filter(AccountClaim.claimed != True) \
        .filter(AccountClaim.created > expires).all()

        if claims:
            raise ClaimExistsException('Similar claim {} has already been initiated.'.format(claimtype))

        """
        no claim exists create new one
        """
        claim = AccountClaim()
        claim.created = current_time
        claim.expiration = current_time + datetime.timedelta(hours=expiration_hours)
        claim.token = str(uuid.uuid4()).replace('-', '')
        claim.account_claim_type = claimtype
        claim.user = user
        db.session().add(claim)
        db.session().commit()  # <-- explicit commit

        return claim

