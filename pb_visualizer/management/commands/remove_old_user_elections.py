from django.core.management.base import BaseCommand, CommandError
from pb_visualizer.models import Election
from datetime import datetime, timedelta



def remove_old_user_elections():
    query = Election.objects.using("user_submitted").filter(modification_date__lte=datetime.now()-timedelta(days=2))
    for election in query:
        print(f"removing user submitted election {election}")
        election.delete()


class Command(BaseCommand):
    help = 'Delete old user submitted elections'

    def handle(self, *args, **options):
        remove_old_user_elections()