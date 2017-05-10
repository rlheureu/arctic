'''
Created on Oct 7, 2015

@author: shanrandhawa
'''
import time




def retry_func(num_retry, wait_seconds, func, *args,**kwargs):
    """
    will retry function (func) number of times specified and will wait between retries
    
    function must raise exception if it is considered failed
    """
    attempt = 0
    while 1:
        attempt += 1
        try:
            return func(*args, **kwargs)
        except:
            print 'Retry failed attempt {} out of {}.'.format(attempt, num_retry)
            if attempt < num_retry:
                time.sleep(wait_seconds)
                continue
            else:
                # raise whatever the exception may be
                raise

