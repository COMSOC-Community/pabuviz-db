import os

from django.contrib.staticfiles import finders
from django.db.models import Model
from pabutools.election import parse_pabulib

from pb_visualizer.models import Election
from pb_visualizer.pabutools import election_object_to_pabutools

from rest_framework.exceptions import PermissionDenied
from rest_framework import status


class ApiExcepetion(PermissionDenied):
    """Exception to be sent back as a response with the detail as error message."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bad request"
    default_code = "invalid"

    def __init__(self, detail, status_code=None):
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code



def print_if_verbose(string, required_verbosity=1, verbosity=1.0, persist=False):
    if verbosity < required_verbosity:
        return
    elif verbosity == required_verbosity and not persist:
        print(string.ljust(80), end="\r")
    else:
        print(string.ljust(80))


def exists_in_database(model_class: type[Model], database="default", **filters):
    query = model_class.objects.using(database).filter(**filters)
    return query.exists()


class LazyElectionParser:
    def __init__(self, election_obj: Election, use_db, verbosity: int = 1):
        self.election_obj = election_obj
        self.instance = None
        self.profile = None
        self.use_db = use_db
        self.verbosity = verbosity

    def get_election_obj(self):
        return self.election_obj

    def get_parsed_election(self):
        if not self.instance or not self.profile:
            if self.use_db:
                print_if_verbose("translating model...", 1, self.verbosity)
                self.instance, self.profile = election_object_to_pabutools(
                    self.election_obj
                )
            else:
                file_path = finders.find(
                    os.path.join("data", self.election_obj.file_name)
                )
                self.instance, self.profile = parse_pabulib(file_path)
        return self.instance, self.profile
