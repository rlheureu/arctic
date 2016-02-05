"""
database.py
Database configuration
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# default DB config
MYSQL_DATABASE_HOST = os.environ['DB_HOST']
MYSQL_DATABASE_PORT = os.environ['DB_PORT']
MYSQL_DATABASE_USER = os.environ['DB_USER']
MYSQL_DATABASE_PASSWORD = os.environ['DB_PASSWORD']
MYSQL_DATABASE_DB = os.environ['DB']

DEFAULT_ENGINE_DEF ='mysql+mysqldb://{}:{}@{}/{}'.format(MYSQL_DATABASE_USER,
                                                 MYSQL_DATABASE_PASSWORD,
                                                 MYSQL_DATABASE_HOST,
                                                 MYSQL_DATABASE_DB)

class Database:
    """
    This class should be used to obtain the session, this will allow the session
    to be initialized with the necessary values or parameters
    """

    def __init__(self, engine_str = DEFAULT_ENGINE_DEF):
        self.engine = create_engine(engine_str, convert_unicode=True, pool_size=20, pool_recycle=3600)
        self.session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=self.engine))

    def set_session(self, session):
        """
        Used for testing!
        """
        self.session = session
    
    def get_engine(self):
        return self.engine
    
    def session(self):
        return self.session
        
db = Database()
        