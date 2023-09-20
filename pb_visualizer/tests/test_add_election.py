from django.test import TestCase
from pb_visualizer.management.commands.add_election import add_dataset
from pb_visualizer.management.commands.initialize_db import initialize_db
from pb_visualizer.models import *
import os


# Create your tests here.
class AddElectionTestCase(TestCase):
    def setUp(self):
        initialize_db()

    def test_integrity(self):
        """test integrity of election even if pb file has integrity errors"""
        add_dataset(
            "pb_visualizer/tests/test_files/test_file_non_integral_data.pb",
            None,
            verbosity=0,
        )
        election = Election.objects.get(name="election1")

        assert election.num_projects == election.projects.count()
        assert election.num_votes == election.voters.count()
        assert election.has_categories
        assert election.has_targets
        assert election.has_voting_methods
        assert election.has_neighborhoods
        assert election.rule == Rule.objects.get(abbreviation="greedy_cost")

    def test_missing_data(self):
        """election without budget is rejected"""
        self.assertRaises(
            Exception,
            lambda: add_dataset(
                "pb_visualizer/tests/test_files/test_file_missing_budget.pb",
                None,
                verbosity=0,
            ),
        )

    def test_ordinal_example(self):
        """test if importing ordinal preferences works"""
        add_dataset(
            "pb_visualizer/tests/test_files/test_file_ordinal.pb", None, verbosity=0
        )
        election = Election.objects.get(name="election4")
        voter = Voter.objects.get(election=election, voter_id="85")
        project = Project.objects.get(election=election, project_id="6")
        assert (
            PreferenceInfo.objects.get(voter=voter, project=project).preference_strength
            == 3
        )

    def test_cumulative_example(self):
        """test if importing ordinal preferences works"""
        add_dataset(
            "pb_visualizer/tests/test_files/test_file_cumulative.pb", None, verbosity=0
        )
        election = Election.objects.get(name="election5")
        voter = Voter.objects.get(election=election, voter_id="15393")
        project = Project.objects.get(election=election, project_id="2")
        assert (
            PreferenceInfo.objects.get(voter=voter, project=project).preference_strength
            == 2
        )

    # def tearDown(self) -> None:
    #     return super().tearDown()
