import pabutools.fractions as fractions
from django.core.management.base import BaseCommand
from pb_visualizer.management.commands.utils import (
    LazyElectionParser,
    exists_in_database,
    print_if_verbose,
)
from pb_visualizer.models import *
from pb_visualizer.pabutools import (
    instance_property_mapping,
    profile_property_mapping,
)


def export_election_properties(
    export_file: str,
    election_names: list[str]|None = None,
    database: str = "default",
    verbosity=1,
) -> None:
    election_query = Election.objects.using(database).all()
    if election_names is not None:
        election_query = election_query.filter(name__in=election_names)
    n_elections = len(election_query)

    headers = ["election_name", "property_short_name", "value"]
    with open(export_file, "w") as f:
        f.write(";".join(headers) + "\n")

    for index, election_obj in enumerate(election_query):
        print_if_verbose(
            f"Exporting instance and profile properties of election {index + 1}/{n_elections}: {election_obj.name}",
            1,
            verbosity,
            persist=True,
        )

        # we first compute the instance properties
        for instance_property in instance_property_mapping:
            metadata_obj = ElectionMetadata.objects.using(database).get(short_name=instance_property)
            if metadata_obj.applies_to_election(election_obj):
                election_prop_obj = ElectionDataProperty.objects.using(database).filter(election=election_obj, metadata=metadata_obj)
                if election_prop_obj.exists():
                    election_prop_obj = election_prop_obj.first()
                    with open(export_file, "a") as f:
                        f.write(f'"{election_obj.name}";{instance_property};{election_prop_obj.value}\n')

        # we now compute the profile properties
        for profile_property in profile_property_mapping:
            metadata_obj = ElectionMetadata.objects.using(database).get(short_name=profile_property)
            if metadata_obj.applies_to_election(election_obj):
                election_prop_obj = ElectionDataProperty.objects.using(database).filter(election=election_obj, metadata=metadata_obj)
                if election_prop_obj.exists():
                    election_prop_obj = election_prop_obj.first()
                    with open(export_file, "a") as f:
                        f.write(f'"{election_obj.name}";{profile_property};{election_prop_obj.value}\n')


class Command(BaseCommand):
    help = "exports the properties of the elections in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "-e",
            "--election_names",
            nargs="*",
            type=str,
            default=None,
            help="Give a list of election names for which you want to compute properties.",
        )
        parser.add_argument(
            "-f",
            "--file",
            nargs="?",
            type=str,
            default=None,
            help="Specify a file to export the result of the computations instead of storing them in the database.",
        )
        parser.add_argument(
            "--database",
            type=str,
            default="default",
            help="name of the database to compute on",
        )

    def handle(self, *args, **options):

        if options["file"]:
            export_election_properties(
                export_file=options["file"],
                election_names=options["election_names"],
                database=options["database"]
            )
