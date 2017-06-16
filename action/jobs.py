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
import uuid
from datetime import datetime


LOG = logging.getLogger('app')

@async
def start_scheduler():
    
    jobqueue = Queue.Queue()

    """
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # Register jobs here
    """
    schedule.every(6).hours.do(jobqueue.put, price_grabber.sync_prices)

    # main worker thread
    def worker_main():
        while 1:

            job_func = jobqueue.get()
            
            jobid = str(uuid.uuid1())
            starttime = datetime.now()
            LOG.info('Running job at {} name: [{}], id: [{}]'.format(starttime, job_func, jobid))
            
            try:
                # begin transaction
                db.session().close()

                job_func()
                
                #
                # close DB session so transactions are actually committed
                db.session().close()
                
            except Exception:
                
                LOG.exception('Exception occurred while running job name: [{}] id: [{}]. Bad job needs fixing!!'.format(job_func, jobid))
                db.session().rollback()
            
            endtime = datetime.now()
            LOG.info('Done running queued job. Time: {}, ({} seconds), name: [{}], id: [{}]'.format(endtime, (endtime-starttime).seconds, job_func, jobid))


    worker_thread = threading.Thread(target=worker_main)
    worker_thread.start()  ###### TODO: event handling - graceful shutdown
    while 1:
        schedule.run_pending()
        time.sleep(1)