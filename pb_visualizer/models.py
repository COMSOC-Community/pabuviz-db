from django.contrib.auth.models import User
from django.db import models

from .choices import *


# ================================
#    Models related to the data
# ================================

# class DataTag(models.Model):
#     name = models.CharField(max_length=50,
#                             unique=True,
#                             verbose_name="",
# help_text="name")
#     description = models.TextField(
#         verbose_name="",
# help_text="Description of the tag")

#     class Meta:
#         ordering = ['name']

#     def __str__(self):
#         return self.name


class BallotType(models.Model):
    name = models.CharField(max_length=10, unique=True, primary_key=True)
    description = models.TextField()
    order_priority = models.IntegerField()

    class Meta:
        ordering = ["order_priority"]


class RuleFamily(models.Model):
    # rule data
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.SlugField(
        max_length=25, unique=True, verbose_name="abbreviation", primary_key=True
    )
    description = models.TextField(blank=True, verbose_name="")
    # meta data
    order_priority = models.IntegerField(default=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order_priority", "name"]


class Rule(models.Model):
    # rule data
    name = models.CharField(max_length=50)
    abbreviation = models.SlugField(
        max_length=25, unique=True, verbose_name="abbreviation", primary_key=True
    )
    description = models.TextField(blank=True, verbose_name="")
    applies_to = models.ManyToManyField(BallotType, related_name="rules")
    rule_family = models.ForeignKey(
        RuleFamily,
        on_delete=models.CASCADE,
        related_name="elements",
        null=True,
        blank=True,
    )
    # meta data
    order_priority = models.IntegerField(default=100)

    def applies_to_election(self, election):
        return self.applies_to.filter(name=election.ballot_type.name).exists()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order_priority", "name"]


class Election(models.Model):
    # Election data
    name = models.TextField()  # This should be unique but MySQL does not allow it.
    description = models.TextField(blank=True)
    country = models.CharField(max_length=50, blank=True)
    unit = models.CharField(
        max_length=150,
        verbose_name="unit",
        help_text="name of the municipality, region, organization, etc.",
        blank=True,
    )
    subunit = models.CharField(
        max_length=150,
        verbose_name="subunit",
        help_text="name of the sub-jurisdiction",
        blank=True,
    )
    instance = models.SlugField(
        max_length=150,
        verbose_name="instance",
        help_text="identifier from the organizers",
        blank=True,
    )
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="budget",
        help_text="maximum budget to spend",
    )
    ballot_type = models.ForeignKey(
        BallotType,
        on_delete=models.CASCADE,
        related_name="elections",
        verbose_name="ballot type",
    )
    rule = models.ForeignKey(
        Rule,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="elections",
        verbose_name="rule applied",
        help_text="the rule that was applied in the actual election",
    )

    date_begin = models.DateField(
        blank=True,
        null=True,
        verbose_name="start date",
        help_text="start date of the voting process",
    )
    date_end = models.DateField(
        blank=True,
        null=True,
        verbose_name="end date",
        help_text="end date of the voting process",
    )
    language = models.CharField(max_length=50, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    district = models.TextField(blank=True)
    comment = models.TextField(blank=True)

    # Additional (possibly redundant) data
    num_projects = models.IntegerField(verbose_name="number of projects", default=0)
    num_votes = models.IntegerField(verbose_name="number of votes", default=0)

    has_categories = models.BooleanField(
        default=False,
        verbose_name="project categories",
        help_text="each project is assigned one or more project categories",
    )
    has_targets = models.BooleanField(
        default=False,
        verbose_name="project target groups",
        help_text="each project is assigned one or more target groups",
    )
    has_neighborhoods = models.BooleanField(
        default=False,
        verbose_name="neighbourhoods",
        help_text="the voters are divided into neighborhoods",
    )
    has_voting_methods = models.BooleanField(
        default=False,
        verbose_name="voting methods",
        help_text="the voting method (e.g. online vote or in person) is recorded for each vote",
    )

    is_trivial = models.BooleanField(default=False)

    # meta data
    modification_date = models.DateField(auto_now=True)

    file_name = models.CharField(max_length=50, blank=True, null=True, unique=True)
    file_size = models.FloatField(default=0)

    public_fields = [
        "name",
        "description",
        "country",
        "unit",
        "subunit",
        "budget",
        "num_projects",
        "num_votes",
        "ballot_type",
        "rule",
        "date_begin",
        "date_end",
        "has_categories",
        "has_targets",
        "has_neighborhoods",
        "has_voting_methods",
    ]

    def get_meta_property(self, short_name):
        try:
            data_property = self.election_data_properties.get(
                metadata__short_name=short_name
            )
            return data_property.value
        except:
            return None

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-date_begin", "country", "unit"]


class Category(models.Model):
    name = models.CharField(max_length=50)
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="categories"
    )

    class Meta:
        ordering = ["name"]
        unique_together = [["name", "election"]]


class Target(models.Model):
    name = models.CharField(max_length=50)
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="targets"
    )

    class Meta:
        ordering = ["name"]
        unique_together = [["name", "election"]]


class Neighborhood(models.Model):
    name = models.CharField(max_length=50)
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="neighborhoods"
    )

    class Meta:
        ordering = ["name"]
        unique_together = [["name", "election"]]


class VotingMethod(models.Model):
    name = models.CharField(max_length=50)
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="voting_methods"
    )

    class Meta:
        ordering = ["name"]
        unique_together = [["name", "election"]]


class Project(models.Model):
    # rule data
    project_id = models.CharField(
        max_length=20,
        verbose_name="project id",
        help_text="project id specific to the election",
    )
    cost = models.DecimalField(max_digits=15, decimal_places=2)
    name = models.TextField()  # TODO: not obligatory in pabulib standard
    description = models.TextField(default="")  # TODO: not in pabulib standard
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="projects"
    )
    categories = models.ManyToManyField(Category, blank=True, related_name="projects")
    targets = models.ManyToManyField(Target, blank=True, related_name="projects")

    class Meta:
        ordering = ["project_id"]
        unique_together = [["project_id", "election"]]


class Voter(models.Model):
    voter_id = models.CharField(
        max_length=20,
        verbose_name="voter id",
        help_text="voter id specific to the election",
    )
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER, blank=True)
    voting_method = models.ForeignKey(
        VotingMethod,
        on_delete=models.CASCADE,
        related_name="voters",
        blank=True,
        null=True,
    )
    neighborhood = models.ForeignKey(
        Neighborhood,
        on_delete=models.CASCADE,
        related_name="voters",
        blank=True,
        null=True,
    )
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="voters"
    )
    votes = models.ManyToManyField(
        Project, related_name="voters", through="PreferenceInfo"
    )

    class Meta:
        unique_together = [["voter_id", "election"]]


class PreferenceInfo(models.Model):
    voter = models.ForeignKey(
        Voter, on_delete=models.CASCADE, related_name="preference_infos"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="preference_infos"
    )
    preference_strength = models.FloatField(default=1)

    class Meta:
        unique_together = [["voter", "project"]]
        ordering = ["-preference_strength"]


class ElectionMetadata(models.Model):
    name = models.CharField(max_length=50, unique=True)
    short_name = models.CharField(max_length=25, unique=True, primary_key=True)
    description = models.TextField()

    inner_type = models.CharField(max_length=20, choices=INNER_TYPE)
    # range = models.CharField(max_length=10)
    order_priority = models.IntegerField()
    applies_to = models.ManyToManyField(BallotType, related_name="election_metadata")

    def applies_to_election(self, election):
        return self.applies_to.filter(name=election.ballot_type.name).exists()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order_priority", "name"]


class ElectionDataProperty(models.Model):
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="data_properties"
    )
    metadata = models.ForeignKey(
        ElectionMetadata, on_delete=models.CASCADE, related_name="data_properties"
    )
    value = models.FloatField()

    def __str__(self):
        return (
            "Election data property. Election: "
            + self.election.name
            + ", Metadata: "
            + self.metadata.name
            + ". Value: "
            + str(self.value)
        )

    class Meta:
        unique_together = [["election", "metadata"]]
        ordering = ("metadata",)


class RuleResult(models.Model):
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="rule_results"
    )
    rule = models.ForeignKey(
        Rule, on_delete=models.CASCADE, related_name="rule_results"
    )

    selected_projects = models.ManyToManyField(
        Project, related_name="rule_results_selected_by"
    )

    def __str__(self):
        return (
            "Rule result. Election: " + self.election.name + ", Rule: " + self.rule.name
        )

    class Meta:
        unique_together = [["election", "rule"]]
        ordering = ("election", "rule")


class RuleResultMetadata(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=25, unique=True, primary_key=True)
    description = models.TextField()
    inner_type = models.CharField(max_length=20, choices=INNER_TYPE)
    range = models.CharField(max_length=10)
    order_priority = models.IntegerField()
    applies_to = models.ManyToManyField(BallotType, related_name="rule_result_metadata")

    def applies_to_election(self, election):
        return self.applies_to.filter(name=election.ballot_type.name).exists()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order_priority", "name"]


class RuleResultDataProperty(models.Model):
    rule_result = models.ForeignKey(
        RuleResult, on_delete=models.CASCADE, related_name="data_properties"
    )
    metadata = models.ForeignKey(
        RuleResultMetadata, on_delete=models.CASCADE, related_name="data_properties"
    )
    value = models.TextField()

    def __str__(self):
        return (
            "RuleResult data property. Rule: "
            + self.rule_result.rule.name
            + ", Metadata: "
            + self.metadata.name
            + ". Value: "
            + str(self.value)
        )

    class Meta:
        unique_together = [["rule_result", "metadata"]]
        ordering = ("metadata",)


# ==============================
#    Logs for the admin tasks
# ==============================


class Log(models.Model):
    log = models.TextField()
    log_type = models.CharField(max_length=50)
    log_num = models.IntegerField(default=0)
    publication_date = models.DateTimeField()

    class Meta:
        ordering = ["-publication_date"]
        unique_together = [["log_type", "log_num"]]

    def __str__(self):
        return (
            self.log_type
            + " #"
            + str(self.log_num)
            + " - "
            + str(self.publication_date)
        )
