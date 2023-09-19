from django.db.models import Model
from pabutools import rules
from pabutools.analysis import instanceproperties, profileproperties
from pabutools.election import Cardinality_Sat, Cost_Sat, max_budget_allocation_cardinality, max_budget_allocation_cost, \
    Relative_Cost_Approx_Normaliser_Sat, Relative_Cardinality_Sat, CC_Sat

from pb_visualizer.models import Election
from pb_visualizer.pabutools import election_object_to_pabutools

instance_property_mapping = {
    "sum_proj_cost": instanceproperties.sum_project_cost,
    "fund_scarc": instanceproperties.funding_scarcity,
    "avg_proj_cost": instanceproperties.avg_project_cost,
    "med_proj_cost": instanceproperties.median_project_cost,
    "sd_proj_cost": instanceproperties.std_dev_project_cost
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
    "avg_card_sat": {'sat_class': Cardinality_Sat, 'normalizer_func': None},
    "avg_cost_sat": {'sat_class': Cost_Sat, 'normalizer_func': None},
    "avg_nrmcard_sat": {'sat_class': Cardinality_Sat, 'normalizer_func': max_budget_allocation_cardinality},
    "avg_nrmcost_sat": {'sat_class': Cost_Sat, 'normalizer_func': max_budget_allocation_cost},
    "avg_relcard_sat": {'sat_class': Relative_Cardinality_Sat, 'normalizer_func': None},
    "avg_relcost_sat": {'sat_class': Relative_Cost_Approx_Normaliser_Sat, 'normalizer_func': None},
    "happiness": {'sat_class': CC_Sat, 'normalizer_func': None},
}

gini_property_mapping = {
    "equality": Cost_Sat,
    # "fairness": Effort_Sat,
}

def rule_mapping(budget):
    return {
        'greedy_card': {'func': rules.greedy_utilitarian_welfare, 'params': {'sat_class': Cardinality_Sat}},
        'greedy_cost': {'func': rules.greedy_utilitarian_welfare, 'params': {'sat_class': Cost_Sat}},
        'greedy_cc': {'func': rules.greedy_utilitarian_welfare, 'params': {'sat_class': CC_Sat}},
        'max_card': {'func': rules.max_additive_utilitarian_welfare, 'params': {'sat_class': Cardinality_Sat}},
        'max_cost': {'func': rules.max_additive_utilitarian_welfare, 'params': {'sat_class': Cost_Sat}},
        'mes_uncompleted': {'func': rules.method_of_equal_shares, 'params': {'sat_class': Cost_Sat}},
        'mes': {'func': rules.completion_by_rule_combination, 'params': {
            'rule_sequence': [rules.exhaustion_by_budget_increase, rules.greedy_utilitarian_welfare],
            'rule_params': [
                {
                    'rule': rules.method_of_equal_shares,
                    'rule_params': {'sat_class': Cost_Sat},
                    'budget_step': float(budget) / 100
                },
                {"sat_class": Cost_Sat},
            ]
        }},
        'mes_greedy_cost': {'func': rules.completion_by_rule_combination, 'params': {
            'rule_sequence': [rules.method_of_equal_shares, rules.greedy_utilitarian_welfare],
            'rule_params': [{'sat_class': Cost_Sat}, {'sat_class': Cost_Sat}]
        }},
        'seq_phragmen': {'func': rules.sequential_phragmen, 'params': {}}
    }


def print_if_verbose(string, required_verbosity=1, verbosity=1., persist=False):
    if verbosity < required_verbosity:
        return
    elif verbosity == required_verbosity and not persist:
        print(string.ljust(80), end="\r")
    else:
        print(string.ljust(80))


def exists_in_database(model_class: type[Model],
                       **filters):
    query = model_class.objects.filter(**filters)
    return query.exists()


class LazyElectionParser():
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
            self.instance, self.profile = election_object_to_pabutools(self.election_obj)
        return self.instance, self.profile
