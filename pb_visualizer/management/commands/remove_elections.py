from django.core.management.base import BaseCommand

from pb_visualizer.models import *


def remove_elections(election_ids=None, database="default"):
    if election_ids is None:
        print("removing all elections...")
        election_query = Election.objects.using(database).all()
    else:
        election_query = Election.objects.using(database).get(id__in=election_ids)
    for e in election_query:
        print(f"deleting {e}")
        e.delete()


class Command(BaseCommand):
    help = "Removes elections from the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "-e",
            "--election_id",
            nargs="*",
            type=str,
            default=None,
            help="Give a list of election ids which you want to remove. If none is given, all elections are removed.",
        )
        parser.add_argument(
            "--database",
            type=str,
            default="default",
            help="name of the database to delete from",
        )

    def handle(self, *args, **options):
        remove_elections(election_ids=options["election_id"], database=options["database"])
