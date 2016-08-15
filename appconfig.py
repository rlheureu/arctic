'''
Created on Aug 14, 2016

@author: shanrandhawa
'''
import os

def get_env_or_default(configkey, defaultval): return os.environ.get(configkey) if os.environ.get(configkey) else defaultval


BCC_EMAIL_ADDRESS = get_env_or_default('BCC_EMAIL_ADDRESS', 'shanrandhawa@gmail.com')
FULL_APP_URL = 'http://{}'.format(get_env_or_default('FULL_APP_URL', 'localhost:5000'))
APP_EMAILER_NAME = get_env_or_default('APP_EMAILER_NAME', 'Amdahl Cube')
APP_EMAILER_ADDRESS = get_env_or_default('APP_EMAILER_ADDRESS', 'shanrandhawa@gmail.com')
APP_EMAILER_PASSWORD = get_env_or_default('APP_EMAILER_PASSWORD', 'asdfasf')


