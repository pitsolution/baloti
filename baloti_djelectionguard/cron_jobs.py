from apscheduler.schedulers.background import BackgroundScheduler
from djelectionguard.models import ParentContest, Contest, Recommender, ContestType, Initiator
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
            translated_name = GoogleTranslator('auto', language.iso).translate(each.name)
            parentcontest = ParentContesti18n.objects.filter(parent_contest_id=each.pk,language=language)
            if not parentcontest:
                ParentContesti18n.objects.create(parent_contest_id=each,language=language,name= translated_name)

    return True

def contest_autotranslate():

    queryset = Contest.objects.all()
    from .models import Contesti18n
    for each in queryset:
        for language in Language.objects.all():
            contest = Contesti18n.objects.filter(contest_id=each.pk,language=language)
            if not contest:
                translated_name = GoogleTranslator('auto', language.iso).translate(each.name)
                translated_about = GoogleTranslator('auto', language.iso).translate(each.about)
                translated_against = GoogleTranslator('auto', language.iso).translate(each.against_arguments)
                translated_infavour = GoogleTranslator('auto', language.iso).translate(each.infavour_arguments)
                Contesti18n.objects.create(contest_id=each, parent=each.parent, language=language,
                    name= translated_name, against_arguments=translated_against, about=translated_about,
                    infavour_arguments=translated_infavour)

    return True

def Recommenderautotranslate():

    queryset = Recommender.objects.all()
    from .models import Recommenderi18n
    for each in queryset:
        for language in Language.objects.all():
            recommender = Recommenderi18n.objects.filter(recommender_id=each.pk,language=language)
            if not recommender:
                translated_name = GoogleTranslator('auto', language.iso).translate(each.name)
                translated_type = GoogleTranslator('auto', language.iso).translate(each.recommender_type)
                Recommenderi18n.objects.create(recommender_id=each,language=language,name= translated_name, recommender_type=translated_type)

    return True

def ContestTypeautotranslate():

    queryset = ContestType.objects.all()
    from .models import ContestTypei18n
    for each in queryset:
        for language in Language.objects.all():
            contesttype = ContestTypei18n.objects.filter(contest_type_id=each.pk,language=language)
            if not contesttype:
                translated_name = GoogleTranslator('auto', language.iso).translate(each.name)
                ContestTypei18n.objects.create(contest_type_id=each,language=language,name= translated_name)

    return True

def Initiatorautotranslate():

    queryset = Initiator.objects.all()
    languages = Language.objects.all()
    from .models import Initiatori18n
    print('queryset==============================', queryset)
    for each in queryset:
        print('languages============================', languages)
        for language in languages:
            initiator = Initiatori18n.objects.filter(initiator_id=each.pk, language=language)
            print('initiator=============================', initiator)
            if not initiator:
                print('test--------------------------------------------')
                translated_name = GoogleTranslator('auto', language.iso).translate(each.name)
                Initiatori18n.objects.create(initiator_id=each, language=language, name= translated_name)

    return True

def daily_cron():
    # parent_contest_autotranslate()
    # contest_autotranslate()
    # Recommenderautotranslate()
    # ContestTypeautotranslate()
    Initiatorautotranslate()

def minute_cron():
    close_votes()

def initialize_cron():
    """Initializes daily crons
    """
    sched.add_job(minute_cron, trigger='cron', start_date='2022-03-29', day_of_week='mon-sun', minute='*')
    sched.add_job(daily_cron, trigger='cron', start_date='2022-05-09', day_of_week='mon-sun', hour=3, minute=20)
