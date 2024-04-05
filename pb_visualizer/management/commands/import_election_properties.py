import csv

from django.core.management import BaseCommand

from pb_visualizer.management.commands.utils import exists_in_database
from pb_visualizer.models import Election, ElectionMetadata, ElectionDataProperty


def import_election_properties(profile_file_path, override, database="default"):
    with open(profile_file_path, "r") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            election_obj = Election.objects.using(database).get(name=row["election_name"])
            metadata_obj = ElectionMetadata.objects.using(database).get(
                short_name=row["property_short_name"]
            )
            unique_filters = {"election": election_obj, "metadata": metadata_obj}
            if override or not exists_in_database(
                ElectionDataProperty, database, **unique_filters
            ):
                print(f"Importing for {election_obj.name} and {metadata_obj.name}")
                ElectionDataProperty.objects.using(database).update_or_create(
                    **unique_filters, defaults={"value": row["value"]}
                )


class Command(BaseCommand):
    help = (
        "imports the value of the instance and profile properties from a CSV file generated via the command "
        "compute_election_properties into the database"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-p",
            "--profile",
            nargs="?",
            type=str,
            default=None,
            help="The file to read the properties from",
        )
        parser.add_argument(
            "-o",
            "--override",
            nargs="?",
            type=bool,
            const=True,
            default=False,
            help="Override properties that were already computed.",
        )
        parser.add_argument(
            "--database",
            type=str,
            default="default",
            help="name of the database to import to",
        )

    def handle(self, *args, **options):
        if "instfile" not in options and "profile" not in options:
            print("You need to provide at least one of --instfile or --profile")
        else:
            import_election_properties(
                options["profile"], options["override"], options["database"]
            )
