import logging
from logging.handlers import RotatingFileHandler
import os

import cherrypy
from arctic import app
from paste.translogger import TransLogger #@UnresolvedImport

if __name__ == '__main__':

    # if the app is being run through cherrypy it is assumed to be in production
    app.debug = False
    
    # set logger etc - log to file
    file_handler = RotatingFileHandler(os.environ.get('LOG_FILE_PATH') + 'arctic.log', maxBytes=2*1024*1024, backupCount=10)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app = TransLogger(app, logger=app.logger,setup_console_handler=False)

    # Mount the application
    cherrypy.tree.graft(app, "/")

    # Unsubscribe the default server
    cherrypy.server.unsubscribe()

    # Instantiate a new server object
    server = cherrypy._cpserver.Server()

    # Configure the server object
    server.socket_host = "0.0.0.0"
    server.socket_port = 80
    server.thread_pool = 100
    server.show_tracebacks = True

    # For SSL Support
    # server.ssl_module            = 'pyopenssl'
    # server.ssl_certificate       = 'ssl/certificate.crt'
    # server.ssl_private_key       = 'ssl/private.key'
    # server.ssl_certificate_chain = 'ssl/bundle.crt'

    cherrypy.log.screen = True

    # Subscribe this server
    server.subscribe()

    # Start the server engine (Option 1 *and* 2)
    cherrypy.engine.start()
    cherrypy.engine.block()
