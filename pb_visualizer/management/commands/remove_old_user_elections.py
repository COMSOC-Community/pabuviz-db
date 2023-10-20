from django.core.management.base import BaseCommand, CommandError
from pb_visualizer.models import Election
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Delete old user submitted elections'

    def handle(self, *args, **options):
        Election.objects.using("user_submitted").filter(modification_date__lte=datetime.now()-timedelta(days=2)).delete()