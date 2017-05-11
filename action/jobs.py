'''
Created on Oct 7, 2015
@author: shanrandhawa
'''
import Queue
import logging
import threading
import time
import schedule

from database.database import db
from utils.decorators import async
from action import price_grabber


LOG = logging.getLogger('app')

@async
def start_scheduler():
    
    jobqueue = Queue.Queue()

    """
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # Register jobs here
    """
    schedule.every(1).hours.do(jobqueue.put, price_grabber.sync_prices)

    # main worker thread
    def worker_main():
        while 1:

            job_func = jobqueue.get()

            try:
                # begin transaction
                db.session().close()

                job_func()
                #
                # close DB session so transactions are actually committed
                LOG.info('Done running queued job. Closing DB session so transactions can be completed.')
                db.session().close()
            except Exception:
                LOG.exception('Exception occurred while running job. Bad job, needs fixing!!')
                db.session().rollback()


    worker_thread = threading.Thread(target=worker_main)
    worker_thread.start()  ###### TODO: event handling - graceful shutdown
    while 1:
        schedule.run_pending()
        time.sleep(1)