import csv

from django.core.management import BaseCommand

from pb_visualizer.management.commands.utils import exists_in_database
from pb_visualizer.models import Election, Rule, RuleResult, Project


def import_rule_results(file_path, override, database="default"):
    with open(file_path, "r") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            election_obj = Election.objects.using(database).get(name=row["election_name"])
            rule_obj = Rule.objects.using(database).get(abbreviation=row["rule_abbreviation"])
            unique_filters = {"election": election_obj, "rule": rule_obj}
            if override or not exists_in_database(RuleResult, database, **unique_filters):
                print(f"Importing for {election_obj.name} and {rule_obj.name}")
                rule_result_obj, _ = RuleResult.objects.using(database).update_or_create(
                    **unique_filters
                )

                if row["outcome"]:
                    rule_result_obj.selected_projects.set(
                        [
                            Project.objects.using(database).get(
                                election=election_obj, project_id=project
                            )
                            for project in row["outcome"].split("#%#%#")
                        ]
                    )


class Command(BaseCommand):
    help = "imports the outcome of a rule from a CSV file generated via the command compute_rule_results into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            nargs="?",
            type=str,
            help="The file to read the results from.",
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
        import_rule_results(options["file"], options["override"], options["database"])
