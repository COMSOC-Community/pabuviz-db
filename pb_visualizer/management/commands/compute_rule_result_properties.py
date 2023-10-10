import json
from collections.abc import Iterable

import pabutools.fractions as fractions
from django.core.management.base import BaseCommand
from pabutools.analysis import (
    instanceproperties,
    category,
    votersatisfaction,
    satisfaction_histogram,
)
from pabutools.election.instance import max_budget_allocation_cost
from pabutools.election.satisfaction import Cost_Sat

from pb_visualizer.management.commands.utils import (
    LazyElectionParser,
    exists_in_database,
    print_if_verbose,
)
from pb_visualizer.models import *
from pb_visualizer.pabutools import (
    project_object_to_pabutools,
    satisfaction_property_mapping,
    gini_property_mapping,
)


def compute_rule_result_properties(
    election_names=None,
    rule_property_list: Iterable[str] | None = None,
    exact=False,
    override: bool = False,
    use_db: bool = False,
    verbosity=1,
):
    election_query = Election.objects.all()
    if election_names is not None:
        election_query = election_query.filter(name__in=election_names)
    if not exact:
        fractions.FRACTION = "float"
    n_elections = len(election_query)
    for index, election_obj in enumerate(election_query):
        print_if_verbose(
            f"Computing rule results of election {index + 1}/{n_elections}: {election_obj.name}",
            1,
            verbosity,
            persist=True,
        )
        election_parser = LazyElectionParser(election_obj, use_db, 10000)
        election_obj = election_parser.get_election_obj()

        for rule_result_object in RuleResult.objects.filter(election=election_obj):
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

            for property in satisfaction_property_mapping:
                if rule_property_list == None or property in rule_property_list:
                    metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                    if metadata_obj.applies_to_election(election_obj):
                        unique_filters = {
                            "rule_result": rule_result_object,
                            "metadata": metadata_obj,
                        }
                        if override or not exists_in_database(
                            RuleResultDataProperty, **unique_filters
                        ):
                            print_if_verbose(
                                "Computing {}.".format(property), 3, verbosity
                            )
                            instance, profile = election_parser.get_parsed_election()
                            value = votersatisfaction.avg_satisfaction(
                                instance,
                                profile,
                                budget_allocation,
                                satisfaction_property_mapping[property]["sat_class"],
                            )
                            normalizer = 1
                            if (
                                satisfaction_property_mapping[property][
                                    "normalizer_func"
                                ]
                                != None
                            ):
                                normalizer = satisfaction_property_mapping[property][
                                    "normalizer_func"
                                ](instance, instance.budget_limit)

                            RuleResultDataProperty.objects.update_or_create(
                                **unique_filters,
                                defaults={"value": str(float(value / normalizer))},
                            )

            for property in gini_property_mapping:
                if rule_property_list == None or property in rule_property_list:
                    metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                    if metadata_obj.applies_to_election(election_obj):
                        unique_filters = {
                            "rule_result": rule_result_object,
                            "metadata": metadata_obj,
                        }
                        if override or not exists_in_database(
                            RuleResultDataProperty, **unique_filters
                        ):
                            print_if_verbose(
                                "Computing {}.".format(property), 3, verbosity
                            )
                            instance, profile = election_parser.get_parsed_election()
                            value = votersatisfaction.gini_coefficient_of_satisfaction(
                                instance,
                                profile,
                                budget_allocation,
                                gini_property_mapping[property],
                                invert=True,
                            )
                            RuleResultDataProperty.objects.update_or_create(
                                **unique_filters, defaults={"value": str(float(value))}
                            )

            property = "category_prop"
            if rule_property_list is None or property in rule_property_list:
                metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                if (
                    metadata_obj.applies_to_election(election_obj)
                    and election_obj.has_categories
                ):
                    unique_filters = {
                        "rule_result": rule_result_object,
                        "metadata": metadata_obj,
                    }
                    if override or not exists_in_database(
                        RuleResultDataProperty, **unique_filters
                    ):
                        print_if_verbose("Computing {}.".format(property), 3, verbosity)
                        instance, profile = election_parser.get_parsed_election()
                        value = category.category_proportionality(
                            instance, profile, budget_allocation
                        )
                        RuleResultDataProperty.objects.update_or_create(
                            **unique_filters, defaults={"value": str(float(value))}
                        )

            if len(budget_allocation) > 0:
                property = "med_select_cost"
                if rule_property_list is None or property in rule_property_list:
                    metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                    if metadata_obj.applies_to_election(election_obj):
                        unique_filters = {
                            "rule_result": rule_result_object,
                            "metadata": metadata_obj,
                        }
                        if override or not exists_in_database(
                            RuleResultDataProperty, **unique_filters
                        ):
                            print_if_verbose(
                                "Computing {}.".format(property), 3, verbosity
                            )
                            value = instanceproperties.median_project_cost(
                                budget_allocation
                            )
                            RuleResultDataProperty.objects.update_or_create(
                                **unique_filters, defaults={"value": str(float(value))}
                            )

            property = "agg_nrmcost_sat"
            if rule_property_list is None or property in rule_property_list:
                metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                if metadata_obj.applies_to_election(election_obj):
                    unique_filters = {
                        "rule_result": rule_result_object,
                        "metadata": metadata_obj,
                    }
                    if override or not exists_in_database(
                        RuleResultDataProperty, **unique_filters
                    ):
                        print_if_verbose("Computing {}.".format(property), 3, verbosity)
                        instance, profile = election_parser.get_parsed_election()
                        value = satisfaction_histogram(
                            instance,
                            profile,
                            budget_allocation,
                            Cost_Sat,
                            max_satisfaction=max_budget_allocation_cost(
                                instance, instance.budget_limit
                            ),
                            num_bins=21,
                        )
                        RuleResultDataProperty.objects.update_or_create(
                            **unique_filters, defaults={"value": json.dumps(value)}
                        )


def export_rule_result_properties(
    export_file: str,
    election_names=None,
    rule_property_list: Iterable[str] | None = None,
    exact=False,
    use_db: bool = False,
    verbosity=1,
):
    election_query = Election.objects.all()
    if election_names is not None:
        election_query = election_query.filter(name__in=election_names)
    if not exact:
        fractions.FRACTION = "float"
    n_elections = len(election_query)

    headers = ["election_name", "rule_abbreviation", "property_short_name", "value"]
    with open(f"{export_file}", "w") as f:
        f.write(";".join(headers) + "\n")

    for index, election_obj in enumerate(election_query):
        print_if_verbose(
            f"Exporting rule results of election {index + 1}/{n_elections}: {election_obj.name}",
            1,
            verbosity,
            persist=True,
        )
        election_parser = LazyElectionParser(election_obj, use_db, 10000)
        election_obj = election_parser.get_election_obj()

        for rule_result_object in RuleResult.objects.filter(election=election_obj):
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

            for property in satisfaction_property_mapping:
                if rule_property_list == None or property in rule_property_list:
                    metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                    if metadata_obj.applies_to_election(election_obj):
                        unique_filters = {
                            "rule_result": rule_result_object,
                            "metadata": metadata_obj,
                        }
                        print_if_verbose("Computing {}.".format(property), 3, verbosity)
                        instance, profile = election_parser.get_parsed_election()
                        value = votersatisfaction.avg_satisfaction(
                            instance,
                            profile,
                            budget_allocation,
                            satisfaction_property_mapping[property]["sat_class"],
                        )
                        normalizer = 1
                        if (
                            satisfaction_property_mapping[property]["normalizer_func"]
                            != None
                        ):
                            normalizer = satisfaction_property_mapping[property][
                                "normalizer_func"
                            ](instance, instance.budget_limit)

                        with open(f"{export_file}", "a") as f:
                            f.write(
                                f'"{election_obj.name}";{rule_result_object.rule.abbreviation};{property};{float(value / normalizer)}\n'
                            )

            for property in gini_property_mapping:
                if rule_property_list == None or property in rule_property_list:
                    metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                    if metadata_obj.applies_to_election(election_obj):
                        print_if_verbose("Computing {}.".format(property), 3, verbosity)
                        instance, profile = election_parser.get_parsed_election()
                        value = votersatisfaction.gini_coefficient_of_satisfaction(
                            instance,
                            profile,
                            budget_allocation,
                            gini_property_mapping[property],
                            invert=True,
                        )

                        with open(f"{export_file}", "a") as f:
                            f.write(
                                f'"{election_obj.name}";{rule_result_object.rule.abbreviation};{property};{float(value)}\n'
                            )

            property = "category_prop"
            if rule_property_list is None or property in rule_property_list:
                metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                if (
                    metadata_obj.applies_to_election(election_obj)
                    and election_obj.has_categories
                ):
                    print_if_verbose("Computing {}.".format(property), 3, verbosity)
                    instance, profile = election_parser.get_parsed_election()
                    value = category.category_proportionality(
                        instance, profile, budget_allocation
                    )

                    with open(f"{export_file}", "a") as f:
                        f.write(
                            f'"{election_obj.name}";{rule_result_object.rule.abbreviation};{property};{float(value)}\n'
                        )

            if len(budget_allocation) > 0:
                property = "med_select_cost"
                if rule_property_list is None or property in rule_property_list:
                    metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                    if metadata_obj.applies_to_election(election_obj):
                        print_if_verbose("Computing {}.".format(property), 3, verbosity)
                        value = instanceproperties.median_project_cost(
                            budget_allocation
                        )

                        with open(f"{export_file}", "a") as f:
                            f.write(
                                f'"{election_obj.name}";{rule_result_object.rule.abbreviation};{property};{float(value)}\n'
                            )

            property = "agg_nrmcost_sat"
            if rule_property_list is None or property in rule_property_list:
                metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                if metadata_obj.applies_to_election(election_obj):
                    print_if_verbose("Computing {}.".format(property), 3, verbosity)
                    instance, profile = election_parser.get_parsed_election()
                    value = satisfaction_histogram(
                        instance,
                        profile,
                        budget_allocation,
                        Cost_Sat,
                        max_satisfaction=max_budget_allocation_cost(
                            instance, instance.budget_limit
                        ),
                        num_bins=21,
                    )

                    with open(f"{export_file}", "a") as f:
                        f.write(
                            f'"{election_obj.name}";{rule_result_object.rule.abbreviation};{property};{json.dumps(value)}\n'
                        )


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

    def handle(self, *args, **options):
        if options["file"]:
            export_rule_result_properties(
                options["file"],
                election_names=options["election_names"],
                rule_property_list=options["rule_properties"],
                exact=options["exact"],
                use_db=options["usedb"],
            )
        else:
            compute_rule_result_properties(
                election_names=options["election_names"],
                rule_property_list=options["rule_properties"],
                exact=options["exact"],
                override=options["override"],
                verbosity=options["verbosity"],
                use_db=options["usedb"],
            )