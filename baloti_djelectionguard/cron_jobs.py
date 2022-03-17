from apscheduler.schedulers.background import BackgroundScheduler
from djelectionguard.models import ParentContest, Contest
from datetime import datetime
from datetime import timedelta
from django.utils import timezone
sched = BackgroundScheduler()
sched.start()

def close_votes():
    date = datetime.now() - timedelta(days = 1)
    parent = ParentContest.objects.filter(status='open', end__lte=date)
    for parent_id in parent.iterator():
        parent_id.status = 'closed'
        parent_id.actual_end = datetime.now()
        parent_id.save()
        contest = Contest.objects.filter(parent=parent_id)
        for contest_id in contest:
            contest_id.actual_end = parent_id.actual_end
            contest_id.save()


    return True

def daily_cron():
    close_votes()

def initialize_cron():
    """Initializes daily crons
    """
    print('timezone=============================================', timezone.now())
    sched.add_job(daily_cron, trigger='cron', start_date='2022-03-16', day_of_week='mon-sun', hour=22, minute=11)
