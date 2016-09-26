'''
Created on Aug 14, 2016

@author: shanrandhawa
'''
import datetime
import logging

import appconfig
from database import dataaccess
from database.serv_account_claims import AccountClaimTypes, AccountClaimService
from service.emails import EmailSendService
from utils import auth_utils
from utils.exception import InvalidInput, ClaimInvalidException


LOG = logging.getLogger('app')

EXPIRATION_PASSWORD_HOURS = 24
EXPIRATION_NEWACCOUNT_HOURS = 168 # 1 week

PASSWORD_RESET_MESSAGE = """
You are receiving this email because you requested a password reset for your Amdahl Cube account.
<br><br>
To reset your password click the following link.
<br><br>
{}
<br><br>
If you did not request to have your password reset, or have any other questions, please contact us by sending an email to support@amdahlcube.com.
<br><br>
"""

def create_reset_url(claimtoken):
    return '{}/claimserv/claim?c={}'.format(appconfig.FULL_APP_URL, claimtoken)

def initiate_password_reset(email_address):
    """
    will register a password reset request for the passed in email address
    """
    LOG.info('Attempting to initialize reset password for email: {}'.format(email_address))
    
    if not auth_utils.is_valid_email(email_address):
        raise InvalidInput('Invalid Email Address!')
    
    user = dataaccess.get_user_by_email(email_address)
    if not user:
        """ fail silently """
        LOG.info('User [{}] does not exist, cannot initiate reset password request.'.format(email_address))
        return
    
    claim = AccountClaimService().create_claim_for_user(user, AccountClaimTypes.FORGOT_PASSWORD, 24)
    
    """
    send email
    """
    emailserv = EmailSendService()
    msg = emailserv.build_message(appconfig.APP_EMAILER_NAME,
                                  [email_address],
                                  PASSWORD_RESET_MESSAGE.format(create_reset_url(claim.token)),
                                  'Amdahl Cube Password Reset')
    emailserv.send_email(msg,
                         appconfig.APP_EMAILER_ADDRESS,
                         appconfig.APP_EMAILER_PASSWORD,
                         [email_address],
                         appconfig.APP_EMAILER_NAME) 

def reset_password(token, password):
    """
    first verify that token is valid
    """
    if not is_valid_token(token):
        raise ClaimInvalidException('Token not valid!')
    
    """
    will modify the user's password if the token is valid
    """
    acctclaimserv = AccountClaimService()
    claim = acctclaimserv.retrieve_claim(token)
    
    """ TODO: should this be done using an action?? """
    claim.user.password = auth_utils.to_hash(password)
    
    acctclaimserv.mark_claimed(claim)
    

def is_valid_token(token):
    """
    true is the token is associated with a password
    reset and request and is not expired.
    """
    acctclaimserv = AccountClaimService()
    claim = acctclaimserv.retrieve_claim(token)
    if not claim: return False
    return acctclaimserv.is_claim_valid(claim)

def retrieve_claim(token):
    return AccountClaimService().retrieve_claim(token)

def retrieve_claim_by_user_id_claim_type(user_id, claim_type):
    return AccountClaimService().retrieve_claim_by_user_id_claim_type(user_id, claim_type)

def verify_email(token):
    """
    this method will verify that an email is valid (part of sign up process)
    """
    
    if is_valid_token(token):
        claim = retrieve_claim(token)
        
        # TODO: this should happen inside a transaction
        
        user = claim.user
        user.confirmed_at = datetime.datetime.now()
        dataaccess.save_user(user)
        
        AccountClaimService().mark_claimed(claim)

def initiate_email_verification(user):
    """
    initiates email verification
    """
    claim = AccountClaimService().create_claim_for_user(user, AccountClaimTypes.EMAIL_VERIFICATION, 24*30)
    
    
    """
    TODO: send email
    """
    
    return claim
    



    
    
    