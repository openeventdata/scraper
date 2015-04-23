from scraper import run_scraper

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(run_scraper, CronTrigger(hour=0))
    scheduler.start()
