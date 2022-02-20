from apscheduler.schedulers.background import BackgroundScheduler
from .models import ParentContest
from datetime import datetime

sched = BackgroundScheduler()
sched.start()

def close_votes():
    votes = ParentContest.objects.filter(status='open', end_lte=datetime.now())
    if votes:
        for each in votes.iterator():
            each.status = 'closed'
            each.actual_end = datetime.now()
            each.save()

    return True

def daily_cron():
    close_votes()

def initialize_cron():
    """Initializes daily crons
    """
    sched.add_job(daily_cron, trigger='cron', start_date='2022-02-18', day_of_week='mon-sun', hour=22, minute=11)
