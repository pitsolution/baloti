from djelectionguard.models import ParentContest, Contest, Recommender, ContestType, Initiator
from baloti_djelectionguard.models import *
from deep_translator import GoogleTranslator
from djlang.models import Language

def parent_contest_autotranslate():
    queryset = ParentContest.objects.all()
    for each in queryset:
        for language in Language.objects.all():
            translated_name = GoogleTranslator('auto', language.iso).translate(each.name)
            parentcontest = ParentContesti18n.objects.filter(parent_contest_id=each.pk,language=language)
            if not parentcontest:
                ParentContesti18n.objects.create(parent_contest_id=each,language=language,name= translated_name)
    return True

def contest_autotranslate():
    queryset = Contest.objects.all()
    for each in queryset:
        for language in Language.objects.all():
            contest = Contesti18n.objects.filter(contest_id=each.pk,language=language)
            if not contest:
                translated_name = GoogleTranslator('auto', language.iso).translate(each.name)
                translated_about = GoogleTranslator('auto', language.iso).translate(each.about) if each.about else None
                translated_against = GoogleTranslator('auto', language.iso).translate(each.against_arguments)
                translated_infavour = GoogleTranslator('auto', language.iso).translate(each.infavour_arguments)
                Contesti18n.objects.create(contest_id=each, parent=each.parent, language=language,
                    name= translated_name, against_arguments=translated_against, about=translated_about,
                    infavour_arguments=translated_infavour)
    return True

def Recommenderautotranslate():
    queryset = Recommender.objects.all()
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
    for each in queryset:
        for language in languages:
            initiator = Initiatori18n.objects.filter(initiator_id=each, language=language)
            if not initiator:
                translated_name = GoogleTranslator('auto', language.iso).translate(each.name)
                Initiatori18n.objects.create(initiator_id=each, language=language, name= translated_name)
    return True