from django.core.management.base import BaseCommand

from pb_visualizer.models import *


def remove_elections(election_ids=None):
    if election_ids is None:
        Election.objects.all().delete()
    else:
        Election.objects.get(id__in=election_ids).delete()


class Command(BaseCommand):
    help = "Removes elections from the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "-e",
            "--election_id",
            nargs="*",
            type=str,
            default=None,
            help="Give a list of election ids which you want to remove.",
        )

    def handle(self, *args, **options):
        remove_elections(election_ids=options["election_id"])
