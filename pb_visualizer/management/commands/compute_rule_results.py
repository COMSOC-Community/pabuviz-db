from django.core.management import BaseCommand
from pabutools import fractions

from pb_visualizer.management.commands.utils import (
    LazyElectionParser,
    exists_in_database,
    print_if_verbose
)
from pb_visualizer.models import Election, Rule, RuleResult, Project
from pb_visualizer.pabutools import rule_mapping


def compute_rule_results(
    election_names=None,
    rule_list=None,
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
            f"Computing rule results of election {index + 1}/{n_elections}: {election_obj.name}\n"
            f"{election_obj.num_votes} voters and {election_obj.num_projects} projects -- {election_obj.ballot_type.name}",
            1,
            verbosity,
            persist=True,
        )
        election_parser = LazyElectionParser(election_obj, use_db, 10000)

        if rule_list is None or len(rule_list) > 0:
            election_obj = election_parser.get_election_obj()

            rules = rule_mapping(election_obj.budget)
            for rule in rules:
                if rule_list is None or rule in rule_list:
                    rule_obj = Rule.objects.filter(abbreviation=rule)
                    if rule_obj.exists():
                        rule_obj = rule_obj.first()
                        if rule_obj.applies_to_election(election_obj):
                            unique_filters = {"election": election_obj, "rule": rule_obj}
                            if override or not exists_in_database(
                                RuleResult, **unique_filters
                            ):
                                print_if_verbose(f"\tComputing {rule}.", 2, verbosity)
                                rule_result_obj, _ = RuleResult.objects.update_or_create(
                                    **unique_filters
                                )
                                instance, profile = election_parser.get_parsed_election()
                                pabutools_result = rules[rule]["func"](
                                    instance, profile, **rules[rule]["params"]
                                )
                                rule_result_obj.selected_projects.set(
                                    [
                                        Project.objects.get(
                                            election=election_obj, project_id=project.name
                                        )
                                        for project in pabutools_result
                                    ]
                                )


def export_rule_results(
    export_file: str,
    election_names=None,
    rule_list=None,
    exact: bool = True,
    use_db: bool = False,
):
    election_query = Election.objects.all()
    if election_names is not None:
        election_query = election_query.filter(name__in=election_names)
    if not exact:
        fractions.FRACTION = "float"
    n_elections = len(election_query)

    headers = ["election_name", "rule_abbreviation", "outcome"]
    with open(export_file, "w") as f:
        f.write(";".join(headers) + "\n")

    for index, election_obj in enumerate(election_query):
        print(
            f"Computing rule results of election {index + 1}/{n_elections}: {election_obj.name}\n"
            f"{election_obj.num_votes} voters and {election_obj.num_projects} projects -- {election_obj.ballot_type.name}"
        )
        election_parser = LazyElectionParser(election_obj, use_db, 10000)

        if rule_list is None or len(rule_list) > 0:
            election_obj = election_parser.get_election_obj()
            rules = rule_mapping(election_obj.budget)
            for rule in rules:
                if rule_list is None or rule in rule_list:
                    rule_obj = Rule.objects.filter(abbreviation=rule)
                    if rule_obj.exists():
                        rule_obj = rule_obj.first()
                        if rule_obj.applies_to_election(election_obj):
                            print(f"\tRunning {rule}...")
                            instance, profile = election_parser.get_parsed_election()
                            pabutools_result = rules[rule]["func"](
                                instance, profile, **rules[rule]["params"]
                            )
                            with open(export_file, "a") as f:
                                f.write(
                                    f'"{election_obj.name}";{rule};"{"#%#%#".join(p.name for p in pabutools_result)}"\n'
                            )


class Command(BaseCommand):
    help = "computes the results of the elections in the database"

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
            "-r",
            "--rules",
            nargs="*",
            type=str,
            default=None,
            help="Give a list of rules for which you want to the results. Discard option to compute all rules, "
            "no parameter to skip the rule computation.",
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
            export_rule_results(
                options["file"],
                election_names=options["election_names"],
                rule_list=options["rules"],
                exact=options["exact"],
                use_db=options["usedb"],
            )
        else:
            compute_rule_results(
                election_names=options["election_names"],
                rule_list=options["rules"],
                exact=options["exact"],
                override=options["override"],
                verbosity=options["verbosity"],
                use_db=options["usedb"],
            )
