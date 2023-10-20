from django.core.management.base import BaseCommand

from pb_visualizer.models import *
from django.conf import settings


def initialize_ballot_types(database='default'):
    ballot_type_objs = {}
    ballot_type_objs["approval"], _ = BallotType.objects.db_manager(database).update_or_create(
        name="approval",
        defaults={
            "description": "voters simply select a set of projects (the ones they approve), potentially with additional constraints",
            "order_priority": 1,
        },
    )

    ballot_type_objs["ordinal"], _ = BallotType.objects.db_manager(database).update_or_create(
        name="ordinal",
        defaults={
            "description": "voters rank in order of preferences some or all of the projects",
            "order_priority": 2,
        },
    )

    ballot_type_objs["cumulative"], _ = BallotType.objects.db_manager(database).update_or_create(
        name="cumulative",
        defaults={
            "description": "voters distribute a given number of points between the projects",
            "order_priority": 3,
        },
    )

    ballot_type_objs["cardinal"], _ = BallotType.objects.db_manager(database).update_or_create(
        name="cardinal",
        defaults={
            "description": "voters specify a score for each project",
            "order_priority": 4,
        },
    )

    return ballot_type_objs


def initialize_election_metadata(ballot_type_objs, database='default'):
    # election metadata for all vote types
    order_priority = 1
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="max_sum_points",
        defaults={
            "name": "maximum allowed total points",
            "description": "maximum number of points distributed by a voter across all projects",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="min_sum_points",
        defaults={
            "name": "minimum allowed total points",
            "description": "minimum number of points that has to be distributed by a voter across all projects",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"]])

    # election metadata for cumulative and cardinal votes
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_ballot_len",
        defaults={
            "name": "average ballot length",
            "description": "number of projects appearing in a ballot on average",
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="med_ballot_len",
        defaults={
            "name": "median ballot length",
            "description": "median number of projects appearing in a ballot",
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_ballot_cost",
        defaults={
            "name": "average ballot cost",
            "description": "average total cost of the projects appearing in a ballot",
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="med_ballot_cost",
        defaults={
            "name": "median ballot cost",
            "description": "median total cost of the projects appearing in a ballot",
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
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_app_score",
        defaults={
            "name": "average approval score",
            "description": "average number of times a project has been approved",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="med_app_score",
        defaults={
            "name": "median approval score",
            "description": "median number of times a project has been approved",
            "inner_type": "int",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_total_score",
        defaults={
            "name": "average total project score",
            "description": "average total number of points received by a project",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.db_manager(database).update_or_create(
        short_name="med_total_score",
        defaults={
            "name": "median total project score",
            "description": "median total number of points received by a project",
            "inner_type": "float",
            "order_priority": order_priority,
        },
    )
    election_metadata_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )


def initialize_rules(ballot_type_objs, database='default'):
    #  rule families
    order_priority = 1
    greedy_obj, _ = RuleFamily.objects.db_manager(database).update_or_create(
        abbreviation="greedy",
        defaults={
            "name": "greedy satisfaction maximiser",
            "description": "greedy approximations of the satisfaction maximiser",
            "order_priority": order_priority,
        },
    )
    greedy_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    max_sat_obj, _ = RuleFamily.objects.db_manager(database).update_or_create(
        abbreviation="max_sat",
        defaults={
            "name": "satisfaction maximiser",
            "description": "exact satisfaction maximisers",
            "order_priority": order_priority,
        },
    )
    max_sat_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    mes_obj, _ = RuleFamily.objects.db_manager(database).update_or_create(
        abbreviation="mes",
        defaults={
            "name": "methods of equal shares",
            "description": "methods of equal shares",
            "order_priority": order_priority,
        },
    )
    mes_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    order_priority += 1
    other_obj, _ = RuleFamily.objects.db_manager(database).update_or_create(
        abbreviation="other",
        defaults={
            "name": "additional procedures",
            "description": "additional procedures",
            "order_priority": order_priority,
        },
    )
    other_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["ordinal"],
            ballot_type_objs["cumulative"],
            ballot_type_objs["cardinal"],
        ]
    )

    #  rule subfamilies
    order_priority += 1
    mes_card_obj, _ = RuleFamily.objects.db_manager(database).update_or_create(
        abbreviation="mes_card",
        defaults={
            "name": "methods of equal shares (card)",
            "description": "methods of equal shares with cardinality satisfaction",
            "order_priority": order_priority,
            "parent_family": mes_obj
        },
    )
    mes_card_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    mes_cost_obj, _ = RuleFamily.objects.db_manager(database).update_or_create(
        abbreviation="mes_cost",
        defaults={
            "name": "methods of equal shares (cost)",
            "description": "methods of equal shares with cost satisfaction",
            "order_priority": order_priority,
            "parent_family": mes_obj
        },
    )
    mes_cost_obj.applies_to.set([ballot_type_objs["approval"]])


    order_priority += 1
    mes_effort_obj, _ = RuleFamily.objects.db_manager(database).update_or_create(
        abbreviation="mes_effort",
        defaults={
            "name": "methods of equal shares (effort)",
            "description": "methods of equal shares with effort satisfaction",
            "order_priority": order_priority,
            "parent_family": mes_obj
        },
    )
    mes_effort_obj.applies_to.set([ballot_type_objs["approval"]])


    order_priority += 1
    mes_sqrt_obj, _ = RuleFamily.objects.db_manager(database).update_or_create(
        abbreviation="mes_sqrt",
        defaults={
            "name": "methods of equal shares (sqrt)",
            "description": "methods of equal shares with sqrt satisfaction",
            "order_priority": order_priority,
            "parent_family": mes_obj
        },
    )
    mes_sqrt_obj.applies_to.set([ballot_type_objs["approval"]])


    # rules

    # approval ballots
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
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
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
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
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="greedy_cc",
        defaults={
            "name": "greedy (Chamberlin-Courant)",
            "description": "greedily selects projects based on the marginal coverage to cost ratio (the coverage of "
            "a project is the number of approvers)",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="max_card",
        defaults={
            "name": "cardinality satisfaction maximiser",
            "description": "selects a feasible set of projects with the maximum total cardinality satisfaction (number "
            "of approved and selected projects)",
            "order_priority": order_priority,
            "rule_family": max_sat_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="max_cost",
        defaults={
            "name": "cost satisfaction maximiser",
            "description": "selects a feasible set of projects with the maximum total cost satisfaction (total cost "
            "of the approved and selected projects)",
            "order_priority": order_priority,
            "rule_family": max_sat_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["approval"]])

    for mes_sat, mes_sat_long, mes_family_obj in [
        ("cost", "cost", mes_cost_obj),
        ("card", "cardinality", mes_card_obj),
        # ("effort", "effort", mes_effort_obj),
        ("sqrt", "cost square root", mes_sqrt_obj),
    ]:
        order_priority += 1
        rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
            abbreviation=f"mes_{mes_sat}",
            defaults={
                "name": f"equal shares ({mes_sat})",
                "description": f"method of equal shares with {mes_sat_long} satisfaction, completed via iterative "
                f"budget increase and greedy ({mes_sat}) completion",
                "order_priority": order_priority,
                "rule_family": mes_family_obj,
            },
        )
        rule_obj.applies_to.set([ballot_type_objs["approval"]])

        order_priority += 1
        rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
            abbreviation=f"mes_{mes_sat}_greedy",
            defaults={
                "name": f"equal shares ({mes_sat}, greedy)",
                "description": f"method of equal shares with {mes_sat_long} satisfaction, completed via greedy "
                f"({mes_sat}) completion",
                "order_priority": order_priority,
                "rule_family": mes_family_obj,
            },
        )
        rule_obj.applies_to.set([ballot_type_objs["approval"]])

        order_priority += 1
        rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
            abbreviation=f"mes_{mes_sat}_uncompleted",
            defaults={
                "name": f"equal shares ({mes_sat}no completion)",
                "description": f"method of equal shares with {mes_sat_long} satisfaction, not completed",
                "order_priority": order_priority,
                "rule_family": mes_family_obj,
            },
        )
        rule_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
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
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="greedy_cardbal",
        defaults={
            "name": "greedy",
            "description": "greedily selects projects based on the total score to cost ratio",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="greedy_cardbal_cc",
        defaults={
            "name": "greedy (Chamberlin-Courant)",
            "description": "greedily selects projects based on the marginal total maximum score of a selected "
            "project to cost ratio",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set(
        [ballot_type_objs["cumulative"], ballot_type_objs["cardinal"]]
    )

    order_priority += 1
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="max_add_card",
        defaults={
            "name": "additive cardinality satisfaction maximiser",
            "description": "selects a feasible set of projects with the maximum total additive cardinality "
            "satisfaction (total score of selected projects)",
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
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="mes_cardbal",
        defaults={
            "name": "equal shares",
            "description": "method of equal shares using the submitted scores as satisfaction, completed via "
            "iterative budget increase and greedy completion",
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
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="mes_cardbal_uncompleted",
        defaults={
            "name": "equal shares (no completion)",
            "description": "method of equal shares using the submitted scores as satisfaction, not completed",
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
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="mes_cardbal_greedy",
        defaults={
            "name": "equal shares (greedy)",
            "description": "method of equal shares using the submitted scores as satisfaction, completed via greedy "
            "completion",
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
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="greedy_borda",
        defaults={
            "name": "greedy Borda",
            "description": "greedily selects projects based on the total Borda score to cost ratio",
            "order_priority": order_priority,
            "rule_family": greedy_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="max_borda",
        defaults={
            "name": "Borda satisfaction maximiser",
            "description": "selects a feasible set of projects with the maximum total Borda satisfaction (total Borda "
            "score of selected projects)",
            "order_priority": order_priority,
            "rule_family": max_sat_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="mes_borda",
        defaults={
            "name": "equal shares (Borda)",
            "description": "method of equal shares with Borda satisfaction, completed via iterative budget increase "
            "and greedy completion",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="mes_borda_uncompleted",
        defaults={
            "name": "equal shares (Borda, no completion)",
            "description": "method of equal shares with Borda satisfaction, not completed",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    rule_obj, _ = Rule.objects.db_manager(database).update_or_create(
        abbreviation="mes_borda_greedy",
        defaults={
            "name": "equal shares (Borda, greedy)",
            "description": "method of equal shares with Borda satisfaction, completed via greedy completion",
            "order_priority": order_priority,
            "rule_family": mes_obj,
        },
    )
    rule_obj.applies_to.set([ballot_type_objs["ordinal"]])


def initialize_rule_result_metadata(ballot_type_objs, database='default'):
    order_priority = 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
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
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
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
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_relcard_sat",
        defaults={
            "name": "average relative cardinality satisfaction",
            "description": "average over all voters of the ratio of the number of approved project selected by the "
            "rule divided by the maximum size of a feasible subset of the ballot",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
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
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_nrmcost_sat",
        defaults={
            "name": "average cost satisfaction (normalized)",
            "description": "average over all voters of the total cost the approved projects that have been selected, "
            "normalized by the highest cost of a feasible budget allocation",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_relcost_sat",
        defaults={
            "name": "average relative cost satisfaction",
            "description": "average over all voters of the ratio of the total cost of the approved project that have "
            "been selected divided by the maximum total cost of a feasible subset of the ballot",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_sat_cardbal",
        defaults={
            "name": "average satisfaction",
            "description": "average total satisfaction of the voters, the satisfaction being the sum of the scores of "
            "the selected projects",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [ballot_type_objs["cardinal"], ballot_type_objs["cumulative"]]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_relsat_cardbal",
        defaults={
            "name": "average relative satisfaction",
            "description": "average over all voters of the ratio of the total score of the selected projects divided "
            "by the maximum total score achievable by a feasible budget allocation",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [ballot_type_objs["cardinal"], ballot_type_objs["cumulative"]]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="avg_borda_sat",
        defaults={
            "name": "average Borda satisfaction",
            "description": "average total satisfaction of the voters, the satisfaction being the sum of the Borda "
            "scores of the selected projects",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="category_prop",
        defaults={
            "name": "category proportionality",
            "description": "average over all categories of the distance between the budget allocated to the category "
            "by the voter and the cost allocated to the category in the budget allocation",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="inverted_cost_gini",
        defaults={
            "name": "inverted cost Gini",
            "description": "inverted Gini coefficient of the cost satisfaction of the voters: the total cost of the "
            "approved projects that have been selected",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="inverted_cardbal_gini",
        defaults={
            "name": "inverted cost Gini",
            "description": "inverted Gini coefficient of the satisfaction of the voters: the total score of the "
            "selected projects",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [ballot_type_objs["cardinal"], ballot_type_objs["cumulative"]]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="inverted_borda_gini",
        defaults={
            "name": "inverted Borda Gini",
            "description": "inverted Gini coefficient of the satisfaction of the voters: the total Borda score of the "
            "selected projects",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="prop_pos_sat",
        defaults={
            "name": "proportion of voters with positive satisfaction",
            "description": "percentage of voters who enjoy positive (thus non-zero) satisfaction for the selected projects",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set(
        [
            ballot_type_objs["approval"],
            ballot_type_objs["cardinal"],
            ballot_type_objs["cumulative"],
        ]
    )

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
        short_name="prop_pos_sat_ord",
        defaults={
            "name": "proportion of voters with positive Borda satisfaction",
            "description": "percentage of voters who enjoy positive (thus non-zero) Borda satisfaction for the selected "
            "projects",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        },
    )
    metadata_obj.applies_to.set([ballot_type_objs["ordinal"]])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
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
    metadata_obj, _ = RuleResultMetadata.objects.db_manager(database).update_or_create(
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


def initialize_db(database = None):
    databases = [database] if database else list(settings.DATABASES.keys())

    for d in databases:
        ballot_type_objs = initialize_ballot_types(d)
        initialize_election_metadata(ballot_type_objs, d)
        initialize_rules(ballot_type_objs, d)
        initialize_rule_result_metadata(ballot_type_objs, d)


class Command(BaseCommand):
    help = "Initializes the database, to be run once at the beginning"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            type=str,
            help="name of the database to initialize, if not provided initializes all of them",
        )
    def handle(self, *args, **options):
        initialize_db(options['database'])
