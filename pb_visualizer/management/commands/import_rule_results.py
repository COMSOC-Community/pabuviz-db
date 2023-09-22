import csv

from django.core.management import BaseCommand

from pb_visualizer.management.commands.utils import exists_in_database
from pb_visualizer.models import Election, Rule, RuleResult, Project


def import_rule_results(file_path, override):
    with open(file_path, "r") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            election_obj = Election.objects.get(name=row["election_name"])
            rule_obj = Rule.objects.get(abbreviation=row["rule_abbreviation"])
            unique_filters = {"election": election_obj, "rule": rule_obj}
            if override or not exists_in_database(
                    RuleResult, **unique_filters
            ):
                rule_result_obj, _ = RuleResult.objects.update_or_create(
                    **unique_filters
                )
                if row["outcome"]:
                    rule_result_obj.selected_projects.set(
                        [
                            Project.objects.get(
                                election=election_obj, project_id=project
                            )
                            for project in row["outcome"].split('#%#%#')
                        ]
                    )


class Command(BaseCommand):
    help = "compute all properties, rules and rule result properties for the elections in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            nargs="?",
            type=str,
            help="Specify a file to export the result of the computations instead of storing them in the database.",
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

    def handle(self, *args, **options):
        import_rule_results(options["file"], options["override"])
