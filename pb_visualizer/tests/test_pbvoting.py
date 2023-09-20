from django.test import TestCase
from pb_visualizer.management.commands.add_election import add_dataset
from pb_visualizer.management.commands.initialize_db import initialize_db
from pb_visualizer.pabutools import election_object_to_pabutools
from pb_visualizer.models import *
import os


class BuildElectionTestCase(TestCase):
    def setUp(self):
        initialize_db()
        add_dataset(
            "pb_visualizer/tests/test_files/test_file_approval.pb", None, verbosity=0
        )

    def test_election_object_to_pabutools(self):
        return
        # TODO
