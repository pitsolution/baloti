from baloti_djelectionguard.utils.translation import parent_contest_autotranslate, contest_autotranslate, \
                        Recommenderautotranslate, ContestTypeautotranslate, Initiatorautotranslate
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Runs elastic search indexing."

    def handle(self, *args, **options):
        print('test----------------------------')
        parent_contest_autotranslate()
        contest_autotranslate()
        Recommenderautotranslate()
        ContestTypeautotranslate()
        Initiatorautotranslate()