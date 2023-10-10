from django.core.management.base import BaseCommand

from django.apps import apps


class Command(BaseCommand):
    help = "Empty the content of some tables in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "models", nargs="+", type=str, help="the models to be emptied"
        )

    def handle(self, *args, **options):
        for model_name in options["models"]:
            print(f"Emptying model {model_name}")
            model = apps.get_model(app_label="pb_visualizer", model_name=model_name)
            model.objects.all().delete()
            print("\tDone!")
