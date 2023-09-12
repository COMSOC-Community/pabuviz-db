from email.policy import default
from time import sleep
from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.db.models import Max
from numpy import delete

import pb_visualizer

from pb_visualizer.models import *

import traceback
import csv
import os
import datetime

import pprint
from pabutools.election.pabulib import parse_pabulib


def remove_elections(election_ids=None):
    if election_ids == None:
        Election.objects.all().delete()
    else:
        Election.objects.get(id__in=election_ids).delete()


class Command(BaseCommand):
    help = "Removes elections from the database"
    
    def add_arguments(self, parser):
        parser.add_argument('-e','--election_id', nargs='*', type=str, default=None,
                            help="Give a list of election ids which you want to remove.")
    
    def handle(self, *args, **options):
        remove_elections(election_ids=options['election_id'])