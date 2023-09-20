from django.db.models import Model

from pb_visualizer.models import Election
from pb_visualizer.pabutools import election_object_to_pabutools


def print_if_verbose(string, required_verbosity=1, verbosity=1.0, persist=False):
    if verbosity < required_verbosity:
        return
    elif verbosity == required_verbosity and not persist:
        print(string.ljust(80), end="\r")
    else:
        print(string.ljust(80))


def exists_in_database(model_class: type[Model], **filters):
    query = model_class.objects.filter(**filters)
    return query.exists()


class LazyElectionParser:
    def __init__(self, election_obj: Election, verbosity: int = 1):
        self.election_obj = election_obj
        self.instance = None
        self.profile = None
        self.verbosity = verbosity

    def get_election_obj(self):
        return self.election_obj

    def get_parsed_election(self):
        if not self.instance or not self.profile:
            print_if_verbose("translating model...", 1, self.verbosity)
            self.instance, self.profile = election_object_to_pabutools(
                self.election_obj
            )
        return self.instance, self.profile
