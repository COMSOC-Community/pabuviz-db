import pabutools.fractions as fractions
from pabutools import election as pbelection, rules
from pabutools.analysis import instanceproperties, profileproperties
from pabutools.election import (
    Cardinality_Sat,
    Cost_Sat,
    Relative_Cardinality_Sat,
    Relative_Cost_Approx_Normaliser_Sat,
    CC_Sat,
    Additive_Cardinal_Sat,
    Additive_Borda_Sat,
    max_budget_allocation_cardinality,
    max_budget_allocation_cost,
)

from pb_visualizer.models import *

instance_property_mapping = {
    "sum_proj_cost": instanceproperties.sum_project_cost,
    "fund_scarc": instanceproperties.funding_scarcity,
    "avg_proj_cost": instanceproperties.avg_project_cost,
    "med_proj_cost": instanceproperties.median_project_cost,
    "sd_proj_cost": instanceproperties.std_dev_project_cost,
}

profile_property_mapping = {
    "avg_ballot_len": profileproperties.avg_ballot_length,
    "med_ballot_len": profileproperties.median_ballot_length,
    "avg_ballot_cost": profileproperties.avg_ballot_cost,
    "med_ballot_cost": profileproperties.median_ballot_cost,
    "avg_app_score": profileproperties.avg_approval_score,
    "med_app_score": profileproperties.median_approval_score,
    "avg_total_score": profileproperties.avg_total_score,
    "med_total_score": profileproperties.median_total_score,
}

satisfaction_property_mapping = {
    "avg_card_sat": {"sat_class": Cardinality_Sat, "normalizer_func": None},
    "avg_cost_sat": {"sat_class": Cost_Sat, "normalizer_func": None},
    "avg_nrmcard_sat": {
        "sat_class": Cardinality_Sat,
        "normalizer_func": max_budget_allocation_cardinality,
    },
    "avg_nrmcost_sat": {
        "sat_class": Cost_Sat,
        "normalizer_func": max_budget_allocation_cost,
    },
    "avg_relcard_sat": {"sat_class": Relative_Cardinality_Sat, "normalizer_func": None},
    "avg_relcost_sat": {
        "sat_class": Relative_Cost_Approx_Normaliser_Sat,
        "normalizer_func": None,
    },
    "happiness": {"sat_class": CC_Sat, "normalizer_func": None},
}

gini_property_mapping = {
    "equality": Cost_Sat,
    # "fairness": Effort_Sat,
}


def rule_mapping(budget):
    return {
        # approval
        "greedy_card": {
            "func": rules.greedy_utilitarian_welfare,
            "params": {"sat_class": Cardinality_Sat},
        },
        "greedy_cost": {
            "func": rules.greedy_utilitarian_welfare,
            "params": {"sat_class": Cost_Sat},
        },
        "greedy_cc": {
            "func": rules.greedy_utilitarian_welfare,
            "params": {"sat_class": CC_Sat},
        },
        "max_card": {
            "func": rules.max_additive_utilitarian_welfare,
            "params": {"sat_class": Cardinality_Sat},
        },
        "max_cost": {
            "func": rules.max_additive_utilitarian_welfare,
            "params": {"sat_class": Cost_Sat},
        },
        "mes_uncompleted": {
            "func": rules.method_of_equal_shares,
            "params": {"sat_class": Cost_Sat},
        },
        "mes": {
            "func": rules.completion_by_rule_combination,
            "params": {
                "rule_sequence": [
                    rules.exhaustion_by_budget_increase,
                    rules.greedy_utilitarian_welfare,
                ],
                "rule_params": [
                    {
                        "rule": rules.method_of_equal_shares,
                        "rule_params": {"sat_class": Cost_Sat},
                        "budget_step": float(budget) / 100,
                    },
                    {"sat_class": Cost_Sat},
                ],
            },
        },
        "mes_greedy_cost": {
            "func": rules.completion_by_rule_combination,
            "params": {
                "rule_sequence": [
                    rules.method_of_equal_shares,
                    rules.greedy_utilitarian_welfare,
                ],
                "rule_params": [{"sat_class": Cost_Sat}, {"sat_class": Cost_Sat}],
            },
        },
        "seq_phragmen": {"func": rules.sequential_phragmen, "params": {}},
        # cardinal
        "greedy_cardbal": {
            "func": rules.greedy_utilitarian_welfare,
            "params": {"sat_class": Additive_Cardinal_Sat},
        },
        "greedy_cardbal_cc": {
            "func": rules.greedy_utilitarian_welfare,
            "params": {"sat_class": CC_Sat},
        },
        "max_add_card": {
            "func": rules.max_additive_utilitarian_welfare,
            "params": {"sat_class": Additive_Cardinal_Sat},
        },
        "mes_cardbal_uncompleted": {
            "func": rules.method_of_equal_shares,
            "params": {"sat_class": Additive_Cardinal_Sat},
        },
        "mes_cardbal": {
            "func": rules.completion_by_rule_combination,
            "params": {
                "rule_sequence": [
                    rules.exhaustion_by_budget_increase,
                    rules.greedy_utilitarian_welfare,
                ],
                "rule_params": [
                    {
                        "rule": rules.method_of_equal_shares,
                        "rule_params": {"sat_class": Additive_Cardinal_Sat},
                        "budget_step": float(budget) / 100,
                    },
                    {"sat_class": Additive_Cardinal_Sat},
                ],
            },
        },
        "mes_cardbal_greedy": {
            "func": rules.completion_by_rule_combination,
            "params": {
                "rule_sequence": [
                    rules.method_of_equal_shares,
                    rules.greedy_utilitarian_welfare,
                ],
                "rule_params": [
                    {"sat_class": Additive_Cardinal_Sat},
                    {"sat_class": Additive_Cardinal_Sat},
                ],
            },
        },
        # ordinal
        "greedy_borda": {
            "func": rules.greedy_utilitarian_welfare,
            "params": {"sat_class": Additive_Borda_Sat},
        },
        "max_borda": {
            "func": rules.max_additive_utilitarian_welfare,
            "params": {"sat_class": Additive_Borda_Sat},
        },
        "mes_borda_uncompleted": {
            "func": rules.method_of_equal_shares,
            "params": {"sat_class": Additive_Borda_Sat},
        },
        "mes_borda": {
            "func": rules.completion_by_rule_combination,
            "params": {
                "rule_sequence": [
                    rules.exhaustion_by_budget_increase,
                    rules.greedy_utilitarian_welfare,
                ],
                "rule_params": [
                    {
                        "rule": rules.method_of_equal_shares,
                        "rule_params": {"sat_class": Additive_Borda_Sat},
                        "budget_step": float(budget) / 100,
                    },
                    {"sat_class": Additive_Borda_Sat},
                ],
            },
        },
        "mes_borda_greedy": {
            "func": rules.completion_by_rule_combination,
            "params": {
                "rule_sequence": [
                    rules.method_of_equal_shares,
                    rules.greedy_utilitarian_welfare,
                ],
                "rule_params": [
                    {"sat_class": Additive_Borda_Sat},
                    {"sat_class": Additive_Borda_Sat},
                ],
            },
        },
    }


def project_object_to_pabutools(project: Project):
    return pbelection.Project(
        project.project_id,
        fractions.str_as_frac(str(project.cost)),
        [category.name for category in project.categories.all()],
        [target.name for target in project.targets.all()],
    )


def election_object_to_pabutools(
    election: Election,
) -> tuple[pbelection.Instance, pbelection.Profile]:
    categories = {cat.name for cat in election.categories.all()}
    targets = {tar.name for tar in election.targets.all()}
    projects = {
        project.project_id: project_object_to_pabutools(project)
        for project in election.projects.all()
    }

    instance = pbelection.Instance(
        budget_limit=fractions.str_as_frac(str(election.budget)),
        categories=categories,
        targets=targets,
    )
    instance.update(projects.values())

    profile = None
    if election.ballot_type.name == "approval":
        profile = pbelection.ApprovalMultiProfile(
            legal_min_length=election.get_meta_property("min_length"),
            legal_max_length=election.get_meta_property("max_length"),
            legal_min_cost=election.get_meta_property("min_cost"),
            legal_max_cost=election.get_meta_property("max_cost"),
        )
        for voter in election.voters.all():
            profile.append(
                pbelection.FrozenApprovalBallot(
                    [projects[project.project_id] for project in voter.votes.all()]
                )
            )
    elif election.ballot_type.name == "ordinal":
        profile = pbelection.OrdinalProfile(
            legal_min_length=election.get_meta_property("min_length"),
            legal_max_length=election.get_meta_property("max_length"),
        )
        for voter in election.voters.all():
            profile.append(
                pbelection.OrdinalBallot(
                    [
                        projects[pref.project.project_id]
                        for pref in voter.preference_infos.all()
                    ]
                )
            )
    elif election.ballot_type.name == "cumulative":
        profile = pbelection.CumulativeProfile(
            legal_min_length=election.get_meta_property("min_length"),
            legal_max_length=election.get_meta_property("max_length"),
            legal_min_score=election.get_meta_property("min_points"),
            legal_max_score=election.get_meta_property("max_points"),
            legal_min_total_score=election.get_meta_property("min_sum_points"),
            legal_max_total_score=election.get_meta_property("max_sum_points"),
        )
        for voter in election.voters.all():
            profile.append(
                pbelection.CumulativeBallot(
                    {
                        projects[pref.project.project_id]: pref.preference_strength
                        for pref in voter.preference_infos.all()
                    }
                )
            )
    elif election.ballot_type.name == "cardinal":
        profile = pbelection.CardinalProfile(
            legal_min_length=election.get_meta_property("min_length"),
            legal_max_length=election.get_meta_property("max_length"),
            legal_min_score=election.get_meta_property("min_points"),
            legal_max_score=election.get_meta_property("max_points"),
        )
        for voter in election.voters.all():
            profile.append(
                pbelection.CardinalBallot(
                    {
                        projects[pref.project.project_id]: pref.preference_strength
                        for pref in voter.preference_infos.all()
                    }
                )
            )

    return instance, profile
