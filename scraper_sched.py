from functools import wraps
import errno
import os
import signal
from scraper import run_scraper

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


class TimeoutError(Exception):
    pass


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            #signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


@timeout(seconds=90 * 60)
def timeout_runner():
    run_scraper()


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(timeout_runner, CronTrigger(minute=0))
    scheduler.start()
