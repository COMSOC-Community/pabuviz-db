from django.core.management.base import BaseCommand

from pb_visualizer.models import *


def initialize_ballot_types():
    ballot_type_objs = {}

    ballot_type_objs["approval"], _ = BallotType.objects.update_or_create(
        name="approval",
        defaults={"description": "voters simply select a set of projects (the ones they approve), potentially with additional constraints", "order_priority": 1},
    )

    ballot_type_objs["ordinal"], _ = BallotType.objects.update_or_create(
        name="ordinal", defaults={"description": "voters rank in order of preferences some or all of the projects", "order_priority": 2}
    )

    ballot_type_objs["cumulative"], _ = BallotType.objects.update_or_create(
        name="cumulative",
        defaults={"description": "voters distribute a given number of points between the projects", "order_priority": 3},
    )

    ballot_type_objs["cardinal"], _ = BallotType.objects.update_or_create(
        name="cardinal",
        defaults={"description": "voters specify an un-restricted score for a project", "order_priority": 4},
    )

    return ballot_type_objs


def initialize_election_metadata(ballot_type_objs):
    # election metadata for all vote types
    order_priority = 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="max_length",
        defaults={
            "name": "maximum allowed ballot length",
            "description": "maximum number of projects allowed to appear in a ballot",
            "inner_type": "int",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="min_length",
        defaults={
            "name": "minimum allowed ballot length",
            "description": "minimum number of projects that has to appear in a ballot",
            "inner_type": "int",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    # election metadata for approval votes
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="max_sum_cost",
        defaults={
            "name": "maximum allowed ballot cost",
            "description": "maximum total cost allowed for the projects appearing in a ballot",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="min_sum_cost",
        defaults={
            "name": "minimum allowed ballot cost",
            "description": "minimum total cost that the projects appearing in a ballot has to reach",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    # election metadata for cumulative votes
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="max_sum_points",
        defaults={
            "name": "maximum allowed total points",
            "description": "total number of points distributed by a voter",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="min_sum_points",
        defaults={
            "name": "minimum allowed total points",
            "description": "total number of points that has to be distributed by a voter",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"]])

    # election metadata for cumulative and cardinal votes
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="max_points",
        defaults={
            "name": "maximum allowed points",
            "description": "maximum number of points that can be assigned to a single project",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="min_points",
        defaults={
            "name": "minimum allowed points",
            "description": "minimum number of points that has to be assigned to a single project",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="default_score",
        defaults={
            "name": "default score",
            "description": "default score of a project not appearing in a ballot",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cardinal"]])

    # election analysis
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="sum_proj_cost",
        defaults={
            "name": "total cost of all projects",
            "description": "total cost of all the projects of the election",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="fund_scarc",
        defaults={
            "name": "funding scarcity",
            "description": "ratio between the total cost of the projects and the budget limit",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_proj_cost",
        defaults={
            "name": "average project cost",
            "description": "average cost of the projects of the election",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="med_proj_cost",
        defaults={
            "name": "median project cost",
            "description": "median cost of the projects of the election",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="sd_proj_cost",
        defaults={
            "name": "standard deviation of project costs",
            "description": "standard deviation of the cost of all the projects",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_ballot_len",
        defaults={
            "name": "average ballot length",
            "description": "average length of all submitted ballots",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="med_ballot_len",
        defaults={
            "name": "median ballot length",
            "description": "median length of all submitted ballots",
            "inner_type": "int",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_ballot_cost",
        defaults={
            "name": "average ballot cost",
            "description": "average cost of all submitted ballots",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="med_ballot_cost",
        defaults={
            "name": "median ballot cost",
            "description": "median cost of all submitted ballots",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_app_score",
        defaults={
            "name": "average approval score",
            "description": "average number of approvals over all the projects",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="med_app_score",
        defaults={
            "name": "median approval score",
            "description": "median number of approvals over all the projects",
            "inner_type": "int",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_total_score",
        defaults={
            "name": "average total project score",
            "description": "average total score of all the projects",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="med_total_score",
        defaults={
            "name": "median total project score",
            "description": "median total score of all the projects",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )


def initialize_rules(ballot_type_objs):
    #  rule families
    order_priority = 1
    greedy_obj, _ = RuleFamily.objects.update_or_create(
        abbreviation="greedy",
        defaults={
            "name": "greedy satisfaction maximiser",
            "description": "greedy approximation of the satisfaction maximiser",
            "order_priority": order_priority,
        },
    )

    order_priority += 1
    max_sat_obj, _ = RuleFamily.objects.update_or_create(
        abbreviation="max_sat",
        defaults={
            "name": "satisfaction maximiser",
            "description": "exact satisfaction maximisers",
            "order_priority": order_priority,
        },
    )

    order_priority += 1
    mes_obj, _ = RuleFamily.objects.update_or_create(
        abbreviation="mes",
        defaults={
            "name": "method of equal shares",
            "description": "method of equal shares",
            "order_priority": order_priority,
        },
    )

    order_priority += 1
    other_obj, _ = RuleFamily.objects.update_or_create(
        abbreviation="other",
        defaults={
            "name": "additional procedures",
            "description": "additional procedures",
            "order_priority": order_priority,
        },
    )

    # rules

    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="greedy_card",
        defaults={
            "name": "greedy (card)",
            "description": "greedily selects projects based on the approval score to cost ratio",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="greedy_cost",
        defaults={
            "name": "greedy (cost)",
            "description": "greedily selects projects based on the cost to cost ratio, i.e., the approval score",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="greedy_cc",
        defaults={
            "name": "greedy (Chamberlin-Courant)",
            "description": "greedily selects projects based on the covering to cost ratio",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="max_card",
        defaults={
            "name": "cardinality satisfaction maximiser",
            "description": "selects a feasible set of projects with the maximum total cardinality satisfaction (number of approved and selected projects)",
            "order_priority": order_priority,
            "rule_family": max_sat_obj,
        },
    )
    rule_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
        ]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="max_cost",
        defaults={
            "name": "cost satisfaction maximiser",
            "description": "selects a feasible set of projects with the maximum total cost satisfaction (total cost of the approved and selected projects)",
            "order_priority": order_priority,
            "rule_family": max_sat_obj,
        },
    )
    rule_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
        ]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="mes",
        defaults={
            "name": "equal shares",
            "description": "method of equal shares with iterative budget increase and greedy (cost) completion",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
        ]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="mes_uncompleted",
        defaults={
            "name": "equal shares (no completion)",
            "description": "method of equal shares without iterative budget increase or completion",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
        ]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="mes_greedy_cost",
        defaults={
            "name": "equal shares (greedy)",
            "description": "method of equal shares with greedy (cost) completion",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
        ]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="seq_phragmen",
        defaults={
            "name": "sequential Phragmen",
            "description": "sequential Phragmen rule",
            "order_priority": order_priority,
            "rule_family": other_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["approval"]])


def initialize_rule_result_metadata(ballot_type_objs):
    order_priority = 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="average cardinality satisfaction",
        defaults={
            "description": "average number of approved projects selected by the rule over all voters",
            "short_name": "avg_card_sat",
            "inner_type": "float",
            "range": "0-",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="average cardinality satisfaction (normalized)",
        defaults={
            "description": "average number of approved projects selected by the rule over all voters,"
            "normalized by the maximum number of projects that could be chosen w.r.t. the budget limit",
            "short_name": "avg_nrmcard_sat",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="average relative cardinality satisfaction",
        defaults={
            "description": "average number of approved project selected by the rule, relative to the number over all voters.",
            "short_name": "avg_relcard_sat",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Average cost satisfaction",
        defaults={
            "description": "The average cost satisfaction of the voters",
            "short_name": "avg_cost_sat",
            "inner_type": "float",
            "range": "0-",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Average cost satisfaction (normalized)",
        defaults={
            "description": "The average cost satisfaction of the voters,"
            "normalized by the maximum possible budget allocation cost (w.r.t. the budget limit)",
            "short_name": "avg_nrmcost_sat",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Average relative cost satisfaction",
        defaults={
            "description": "The average relative cost satisfaction of the voters",
            "short_name": "avg_relcost_sat",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Category proportionality",
        defaults={
            "description": "",
            "short_name": "category_prop",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Equality (inverted cost gini)",
        defaults={
            "description": "",
            "short_name": "equality",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    # order_priority += 1
    # metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
    #     name="Fairness (inverted share gini)",
    #     defaults={
    #         "description": "",
    #         "short_name": "fairness",
    #         "inner_type": "float",
    #         "order_priority": order_priority,
    #     }
    # )
    # metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Happiness (%non-empty-handed)",
        defaults={
            "description": "",
            "short_name": "happiness",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Median selected cost",
        defaults={
            "description": "",
            "short_name": "med_select_cost",
            "inner_type": "float",
            "range": "0-",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Aggregated normalized cost satisfaction distribution",
        defaults={
            "description": "The relative number of voters being x %% satisfied for x being 0, 0-5, 5-10, ..., 95-100.",
            "short_name": "agg_nrmcost_sat",
            "inner_type": "list[float]",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )


def initialize_db():
    ballot_type_objs = initialize_ballot_types()
    initialize_election_metadata(ballot_type_objs)
    initialize_rules(ballot_type_objs)
    initialize_rule_result_metadata(ballot_type_objs)


class Command(BaseCommand):
    help = "Initializes the database, to be run once at the beginning"

    def handle(self, *args, **options):
        initialize_db()
