from collections.abc import Iterable

import pabutools.fractions as fractions
from django.core.management.base import BaseCommand

from pb_visualizer.management.commands.utils import (
    LazyElectionParser,
    exists_in_database,
    print_if_verbose,
)
from pb_visualizer.models import *
from pb_visualizer.pabutools import (
    project_object_to_pabutools,
    rule_result_property_mapping,
)


def compute_rule_result_properties(
    election_names: list[str]|None = None,
    rule_property_list: Iterable[str] | None = None,
    exact=False,
    override: bool = False,
    use_db: bool = False,
    database: str = "default",
    verbosity=1,
):
    election_query = Election.objects.using(database).all()
    if election_names is not None:
        election_query = election_query.filter(name__in=election_names)
    if not exact:
        fractions.FRACTION = "float"
    n_elections = len(election_query)
    for index, election_obj in enumerate(election_query):
        print_if_verbose(
            f"Computing rule result properties of election {index + 1}/{n_elections}: {election_obj.name} "
            f"{election_obj.num_votes} voters and {election_obj.num_projects} projects -- {election_obj.ballot_type.name}",
            1,
            verbosity,
            persist=True,
        )
        election_parser = LazyElectionParser(election_obj, use_db, 10000)
        election_obj = election_parser.get_election_obj()

        for rule_result_object in RuleResult.objects.using(database).filter(election=election_obj):
            print_if_verbose(
                "Computing properties for {} results.".format(
                    rule_result_object.rule.abbreviation
                ),
                2,
                verbosity,
            )
            budget_allocation = [
                project_object_to_pabutools(project)
                for project in rule_result_object.selected_projects.all()
            ]

            for property, prop_func in rule_result_property_mapping.items():
                if rule_property_list == None or property in rule_property_list:
                    metadata_obj = RuleResultMetadata.objects.using(database).get(short_name=property)
                    if metadata_obj.applies_to_election(election_obj):
                        unique_filters = {
                            "rule_result": rule_result_object,
                            "metadata": metadata_obj,
                        }
                        if override or not exists_in_database(
                            RuleResultDataProperty, database, **unique_filters
                        ):
                            print_if_verbose(
                                "Computing {}.".format(property), 3, verbosity
                            )
                            instance, profile = election_parser.get_parsed_election()
                            try:
                                value = prop_func(instance, profile, budget_allocation)
                                RuleResultDataProperty.objects.using(database).update_or_create(
                                    **unique_filters,
                                    defaults={"value": str(value)},
                                )
                            except Exception as e:
                                print(e)


def export_rule_result_properties(
    export_file: str,
    election_names: list[str]|None = None,
    rule_property_list: Iterable[str] | None = None,
    exact=False,
    use_db: bool = False,
    database: str = "default",
):
    election_query = Election.objects.using(database).all()
    if election_names is not None:
        election_query = election_query.filter(name__in=election_names)
    if not exact:
        fractions.FRACTION = "float"
    n_elections = len(election_query)

    headers = ["election_name", "rule_abbreviation", "property_short_name", "value"]
    with open(f"{export_file}", "w") as f:
        f.write(";".join(headers) + "\n")

    for index, election_obj in enumerate(election_query):
        print(f"Exporting rule results of election {index + 1}/{n_elections}: {election_obj.name}\n"
              f"{election_obj.num_votes} voters and {election_obj.num_projects} projects -- "
              f"{election_obj.ballot_type.name}"
        )
        election_parser = LazyElectionParser(election_obj, use_db, 10000)
        election_obj = election_parser.get_election_obj()

        for rule_result_object in RuleResult.objects.using(database).filter(election=election_obj):
            print(f"\tComputing properties for the result of {rule_result_object.rule.abbreviation}")
            budget_allocation = [
                project_object_to_pabutools(project)
                for project in rule_result_object.selected_projects.all()
            ]

            for property, prop_func in rule_result_property_mapping.items():
                if rule_property_list == None or property in rule_property_list:
                    metadata_obj = RuleResultMetadata.objects.using(database).get(short_name=property)
                    if metadata_obj.applies_to_election(election_obj):
                        print(f"\t\tProperty: {property}")
                        instance, profile = election_parser.get_parsed_election()
                        try:
                            value = prop_func(instance, profile, budget_allocation)
                            with open(f"{export_file}", "a") as f:
                                f.write(
                                    f'"{election_obj.name}";{rule_result_object.rule.abbreviation};{property};{str(value)}\n'
                                )
                        except Exception as e:
                            print(e)


class Command(BaseCommand):
    help = "computes the properties of the results of the ections in the database"

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
            "-p",
            "--rule_properties",
            nargs="*",
            type=str,
            default=None,
            help="Give a list of rule properties which you want to compute. Discard option to compute all properties, no parameter to skip the property computation",
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
            export_rule_result_properties(
                options["file"],
                election_names=options["election_names"],
                rule_property_list=options["rule_properties"],
                exact=options["exact"],
                use_db=options["usedb"],
                database=options["database"]
            )
        else:
            compute_rule_result_properties(
                election_names=options["election_names"],
                rule_property_list=options["rule_properties"],
                exact=options["exact"],
                override=options["override"],
                verbosity=options["verbosity"],
                use_db=options["usedb"],
                database=options["database"]
            )
