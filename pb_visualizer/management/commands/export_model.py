import csv

from django.core.management.base import BaseCommand

from django.apps import apps


class Command(BaseCommand):
    help = "Write a given model into a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("-m", nargs="+", type=str, help="the models to be exported")
        parser.add_argument(
            "-f", nargs="?", default="", type=str, help="the prefix for the file path"
        )
        parser.add_argument(
            "--database",
            type=str,
            default="default",
            help="name of the database to export from",
        )

    def handle(self, *args, **options):
        if not options["m"]:
            print(
                "ERROR: you need to pass a model as input using arugment -m <MODEL_NAME>."
            )
            return
        for model_name in options["m"]:
            model = apps.get_model(app_label="pb_visualizer", model_name=model_name)
            file_prefix = options["f"] + ("_" if len(options["f"]) > 0 else "")
            with open(f"{file_prefix}{model_name}.csv", "w") as csv_file:
                writer = csv.writer(csv_file)
                field_names = [field.name for field in model._meta.get_fields()]
                writer.writerow(field_names)
                for obj in model.objects.using(options["database"]).all():
                    writer.writerow([getattr(obj, field) for field in field_names])
