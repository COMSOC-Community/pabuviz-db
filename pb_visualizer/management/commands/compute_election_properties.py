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


def compute_election_properties(
    election_names: list[str]|None = None,
    exact: bool = False,
    override: bool = False,
    use_db: bool = False,
    database: str = "default",
    verbosity=1,
) -> None:
    election_query = Election.objects.using(database).all()
    if election_names is not None:
        election_query = election_query.filter(name__in=election_names)
    if not exact:
        fractions.FRACTION = "float"
    n_elections = len(election_query)
    for index, election_obj in enumerate(election_query):
        print_if_verbose(
            f"Computing instance and profile properties of election {index + 1}/{n_elections}: {election_obj.name}",
            1,
            verbosity,
            persist=True,
        )
        election_parser = LazyElectionParser(election_obj, use_db, 10000)

        # we first compute the instance properties
        for instance_property in instance_property_mapping:
            metadata_obj = ElectionMetadata.objects.using(database).get(short_name=instance_property)
            if metadata_obj.applies_to_election(election_obj):
                unique_filters = {"election": election_obj, "metadata": metadata_obj}
                if override or not exists_in_database(
                    ElectionDataProperty, database, **unique_filters
                ):
                    instance, profile = election_parser.get_parsed_election()
                    ElectionDataProperty.objects.using(database).update_or_create(
                        **unique_filters,
                        defaults={
                            "value": instance_property_mapping[instance_property](
                                instance
                            )
                        },
                    )

        # we now compute the profile properties
        for profile_property in profile_property_mapping:
            metadata_obj = ElectionMetadata.objects.using(database).get(short_name=profile_property)
            if metadata_obj.applies_to_election(election_obj):
                unique_filters = {"election": election_obj, "metadata": metadata_obj}
                if override or not exists_in_database(
                    ElectionDataProperty, database, **unique_filters
                ):
                    instance, profile = election_parser.get_parsed_election()
                    ElectionDataProperty.objects.using(database).update_or_create(
                        **unique_filters,
                        defaults={
                            "value": profile_property_mapping[profile_property](
                                instance, profile
                            )
                        },
                    )


def export_election_properties(
    export_file: str,
    election_names: list[str]|None = None,
    exact: bool = False,
    override: bool = False,
    use_db: bool = False,
    database: str = "default",
    verbosity=1,
) -> None:
    election_query = Election.objects.using(database).all()
    if election_names is not None:
        election_query = election_query.filter(name__in=election_names)
    if not exact:
        fractions.FRACTION = "float"
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
        election_parser = LazyElectionParser(election_obj, use_db, 10000)

        # we first compute the instance properties
        for instance_property in instance_property_mapping:
            metadata_obj = ElectionMetadata.objects.using(database).get(short_name=instance_property)
            if metadata_obj.applies_to_election(election_obj):
                instance, profile = election_parser.get_parsed_election()
                prop_value = instance_property_mapping[instance_property](instance)
                with open(export_file, "a") as f:
                    f.write(f'"{election_obj.name}";{instance_property};{prop_value}\n')

        # we now compute the profile properties
        for profile_property in profile_property_mapping:
            metadata_obj = ElectionMetadata.objects.using(database).get(short_name=profile_property)
            if metadata_obj.applies_to_election(election_obj):
                instance, profile = election_parser.get_parsed_election()
                prop_value = profile_property_mapping[profile_property](
                    instance, profile
                )
                with open(export_file, "a") as f:
                    f.write(f'"{election_obj.name}";{profile_property};{prop_value}\n')


class Command(BaseCommand):
    help = "computes the properties of the elections in the database"

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
            "--exact",
            nargs="?",
            type=bool,
            const=True,
            default=False,
            help="Use exact fractions instead of floats for computing results.",
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
            "-f",
            "--file",
            nargs="?",
            type=str,
            default=None,
            help="Specify a file to export the result of the computations instead of storing them in the database.",
        )
        parser.add_argument(
            "--usedb",
            nargs="?",
            type=bool,
            const=True,
            default=False,
            help="Use the databse for recovering an election (if present), or the file stored in the static folder ("
            "default).",
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
                exact=options["exact"],
                use_db=options["usedb"],
                database=options["database"]
            )
        else:
            compute_election_properties(
                election_names=options["election_names"],
                exact=options["exact"],
                override=options["override"],
                verbosity=options["verbosity"],
                use_db=options["usedb"],
                database=options["database"]
            )
