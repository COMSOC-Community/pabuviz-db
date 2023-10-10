from django.core.management.base import BaseCommand

from pb_visualizer.models import *


def initialize_ballot_types():
    ballot_type_objs = {}

    ballot_type_objs["approval"], _ = BallotType.objects.update_or_create(
        name="approval",
        defaults={
            "description": "voters simply select a set of projects (the ones they approve), potentially with additional constraints",
            "order_priority": 1,
        },
    )

    ballot_type_objs["ordinal"], _ = BallotType.objects.update_or_create(
        name="ordinal",
        defaults={
            "description": "voters rank in order of preferences some or all of the projects",
            "order_priority": 2,
        },
    )

    ballot_type_objs["cumulative"], _ = BallotType.objects.update_or_create(
        name="cumulative",
        defaults={
            "description": "voters distribute a given number of points between the projects",
            "order_priority": 3,
        },
    )

    ballot_type_objs["cardinal"], _ = BallotType.objects.update_or_create(
        name="cardinal",
        defaults={
            "description": "voters specify an un-restricted score for a project",
            "order_priority": 4,
        },
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
    election_metadata_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )

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

    # approval ballots
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
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

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
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

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
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

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
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

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
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

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

    # cardinal
    order_priority = 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="greedy_cardbal",
        defaults={
            "name": "greedy",
            "description": "greedily selects projects based on the score to cost ratio",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="greedy_cardbal_cc",
        defaults={
            "name": "greedy (Chamberlin-Courant)",
            "description": "greedily selects projects based on the covering to cost ratio",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="max_add_card",
        defaults={
            "name": "additive cardinality satisfaction maximiser",
            "description": "selects a feasible set of projects with the maximum total additive cardinality satisfaction (total score of selected projects)",
            "order_priority": order_priority,
            "rule_family": max_sat_obj,
        },
    )
    rule_obj.applies_to.set(
        [
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="mes_cardbal",
        defaults={
            "name": "equal shares",
            "description": "method of equal shares with iterative budget increase and greedy completion",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set(
        [
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="mes_cardbal_uncompleted",
        defaults={
            "name": "equal shares (no completion)",
            "description": "method of equal shares without iterative budget increase or completion",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set(
        [
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="mes_cardbal_greedy",
        defaults={
            "name": "equal shares (greedy)",
            "description": "method of equal shares with greedy completion",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set(
        [
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    # ordinal
    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="greedy_borda",
        defaults={
            "name": "greedy Borda",
            "description": "greedily selects projects based on the Borda score to cost ratio",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="max_borda",
        defaults={
            "name": "Borda satisfaction maximiser",
            "description": "selects a feasible set of projects with the maximum total Borda satisfaction (total Borda score of selected projects)",
            "order_priority": order_priority,
            "rule_family": max_sat_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="mes_borda",
        defaults={
            "name": "equal shares (Borda)",
            "description": "method of equal shares with iterative budget increase and greedy completion, using the Borda scoring function",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="mes_borda_uncompleted",
        defaults={
            "name": "equal shares (Borda, no completion)",
            "description": "method of equal shares without iterative budget increase or completion, using the Borda scoring function",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation="mes_borda_greedy",
        defaults={
            "name": "equal shares (Borda, greedy)",
            "description": "method of equal shares with greedy completion, using the Borda scoring function",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])


def initialize_rule_result_metadata(ballot_type_objs):
    order_priority = 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="avg_card_sat",
        defaults={
            "name": "average cardinality satisfaction",
            "description": "average over all voters of the number of approved projects selected by the rule",
            "inner_type": "float",
            "range": "0-",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="avg_nrmcard_sat",
        defaults={
            "name": "average cardinality satisfaction (normalized)",
            "description": "average over all voters of the number of approved projects selected by the rule"
            "normalized by the highest number of projects that can be selected in a feasible budget allocation",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="avg_relcard_sat",
        defaults={
            "name": "average relative cardinality satisfaction",
            "description": "average over all voters of the ratio of the number of approved project selected by the rule divided by the maximum size of a feasible subset of the ballot",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="avg_cost_sat",
        defaults={
            "name": "average cost satisfaction",
            "description": "average over all voters of the total cost the approved projects that have been selected",
            "inner_type": "float",
            "range": "0-",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="avg_nrmcost_sat",
        defaults={
            "name": "average cost satisfaction (normalized)",
            "description": "average over all voters of the total cost the approved projects that have been selected,"
            "normalized by the highest cost of a feasible budget allocation",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="avg_relcost_sat",
        defaults={
            "name": "average relative cost satisfaction",
            "description": "average over all voters of the ratio of the total cost of the approved project that have been selected divided by the maximum total cost of a feasible subset of the ballot",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="category_prop",
        defaults={
            "name": "category proportionality",
            "description": "average over all categories of the distance between the budget allocated to the category by the voter and the cost allocated to the category in the budget allocation",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="equality",
        defaults={
            "name": "equality (inverted cost Gini)",
            "description": "inverted Gini coefficient of the cost satisfaction of the voters: the total cost of the approved projects that have been selected",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    # order_priority += 1
    # metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
    # short_name="fairness",
    #     defaults={
    #         "name"="Fairness (inverted share gini)",
    #         "description": "",
    #         "inner_type": "float",
    #         "order_priority": order_priority,
    #     }
    # )
    # metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="happiness",
        defaults={
            "name": "proportion of non-empty-handed",
            "description": "percentage of voters for whom no project appearing in the ballot has been selected",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        short_name="med_select_cost",
        defaults={
            "name": "median selected cost",
            "description": "median of the cost of the selected projects",
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
        short_name="agg_nrmcost_sat",
        defaults={
            "name": "aggregated normalized cost satisfaction distribution",
            "description": "the relative number of voters being x %% satisfied for x being 0, 0-5, 5-10, ..., 95-100.",
            "inner_type": "list[float]",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])


def initialize_db():
    ballot_type_objs = initialize_ballot_types()
    initialize_election_metadata(ballot_type_objs)
    initialize_rules(ballot_type_objs)
    initialize_rule_result_metadata(ballot_type_objs)


class Command(BaseCommand):
    help = "Initializes the database, to be run once at the beginning"

    def handle(self, *args, **options):
        initialize_db()
