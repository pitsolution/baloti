from apscheduler.schedulers.background import BackgroundScheduler
from djelectionguard.models import ParentContest, Contest
from datetime import datetime
from django.utils import timezone
from deep_translator import GoogleTranslator
from djlang.models import Language
sched = BackgroundScheduler()
sched.start()

def close_votes():
    date = datetime.now()
    parent = ParentContest.objects.filter(status='open', end__lte=date)
    for parent_id in parent.iterator():
        parent_id.status = 'closed'
        parent_id.actual_end = datetime.now()
        parent_id.save()
        contests = Contest.objects.filter(parent=parent_id)
        for contest_id in contests:
            contest_id.actual_end = parent_id.actual_end
            contest_id.save()


    return True

def parent_contest_autotranslate():

    queryset = ParentContest.objects.all()
    from .models import ParentContesti18n
    for each in queryset:
        for language in Language.objects.all():
            trans_content_name = GoogleTranslator('auto', language.iso).translate(each.name)
            ParentContesti18n.objects.create(parent_contest_id=each.pk,language=language,name= trans_content_name)

    return True

def daily_cron():
    close_votes()

def initialize_cron():
    """Initializes daily crons
    """
    #parent_contest_autotranslate()
    sched.add_job(daily_cron, trigger='cron', start_date='2022-03-29', day_of_week='mon-sun', minute='*')
