from django.core.management import BaseCommand
from pabutools import fractions

from pb_visualizer.management.commands.utils import (
    LazyElectionParser,
    exists_in_database,
    print_if_verbose
)
from pb_visualizer.models import Election, Rule, RuleResult, Project
from pb_visualizer.pabutools import rule_mapping


def export_rule_results(
    export_file: str,
    election_names: list[str]|None = None,
    rule_list: list[str]|None = None,
    use_db: bool = False,
    database: str = "default"
):
    election_query = Election.objects.using(database).all()
    if election_names is not None:
        election_query = election_query.filter(name__in=election_names)
    n_elections = len(election_query)

    headers = ["election_name", "rule_abbreviation", "outcome"]
    with open(export_file, "w") as f:
        f.write(";".join(headers) + "\n")

    for index, election_obj in enumerate(election_query):
        print(
            f"exporting rule results of election {index + 1}/{n_elections}: {election_obj.name}\n"
            f"{election_obj.num_votes} voters and {election_obj.num_projects} projects -- {election_obj.ballot_type.name}"
        )
        election_parser = LazyElectionParser(election_obj, use_db, 10000)

        if rule_list is None or len(rule_list) > 0:
            election_obj = election_parser.get_election_obj()
            rules = rule_mapping(election_obj.budget)
            for rule in rules:
                if rule_list is None or rule in rule_list:
                    rule_obj = Rule.objects.using(database).filter(abbreviation=rule)
                    if rule_obj.exists():
                        rule_obj = rule_obj.first()
                        if rule_obj.applies_to_election(election_obj):
                            rule_res_obj = RuleResult.objects.using(database).filter(election=election_obj, rule=rule_obj)
                            if rule_res_obj.exists():
                                rule_res_obj = rule_res_obj.first()
                                selected_projects = [p.project_id for p in rule_res_obj.selected_projects.all()]
                                with open(export_file, "a") as f:
                                    f.write(
                                        f'"{election_obj.name}";{rule};"{"#%#%#".join(selected_projects)}"\n'
                                )


class Command(BaseCommand):
    help = "exports the results of the elections in the database"

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
            "-f",
            "--file",
            nargs="?",
            type=str,
            default=None,
            help="Specify a file to export the result of the computations",
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
            export_rule_results(
                options["file"],
                election_names=options["election_names"],
                rule_list=options["rules"],
                use_db=options["usedb"],                
                database=options["database"]
            )