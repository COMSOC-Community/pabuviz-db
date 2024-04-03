from django.core.management.base import BaseCommand

from pb_visualizer.models import *


def check_for_incomplete_elections(delete=False, database="default"):
    print("searching for incomplete elections...")
    election_query = Election.objects.using(database).all()
    for e in election_query:
        num_voters = Voter.objects.using(database).filter(election=e).count()
        if (e.num_votes != num_voters):
            print(f"incomplete election: id: {e.id}, name: {e.name}, num_votes: {e.num_votes}, number of voters: {num_voters}")
            if delete:
                print(f"removing election")
                e.delete()
                
    print("done")

class Command(BaseCommand):
    help = "Checks for elections whose number of voters differs from their num_votes property. Useful for detecting failed attempts to add an election."

    def add_arguments(self, parser):
        parser.add_argument(
            "-d",
            "--delete",
            nargs="?",
            type=bool,
            const=True,
            default=False,
            help="choose whether ot not to delete the incomplete elections",
        )
        parser.add_argument(
            "--database",
            type=str,
            default="default",
            help="name of the database to check",
        )
        

    def handle(self, *args, **options):
        check_for_incomplete_elections(delete=options["delete"], database=options["database"])
