from importlib import metadata
import time
import json
from typing import Iterable
from django.db.models import Model
from django.core.management.base import BaseCommand
import numpy as np

from pb_visualizer.pabutools import project_object_to_pabutools, election_object_to_pabutools
from pb_visualizer.models import *
from pabutools import election as pbinstance
from pabutools import rules
from pabutools.analysis import instanceproperties, profileproperties, category, votersatisfaction, satisfaction_histogram
from pabutools.election.satisfaction import CC_Sat, Cost_Sat, Cardinality_Sat, Effort_Sat, Relative_Cardinality_Sat, Relative_Cost_Sat, Relative_Cost_Approx_Normaliser_Sat
from pabutools.election.instance import max_budget_allocation_cardinality, max_budget_allocation_cost
import pabutools.fractions as fractions


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
    "avg_app_score":  profileproperties.avg_approval_score,
    "med_app_score":  profileproperties.median_approval_score,
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
                    'budget_step': float(budget)/100
                },
                {"sat_class": Cost_Sat},
            ]
        }},
        'mes_greedy_app': {'func': rules.completion_by_rule_combination, 'params': {
            'rule_sequence': [rules.method_of_equal_shares, rules.greedy_utilitarian_welfare],
            'rule_params': [{'sat_class': Cost_Sat}, {'sat_class': Cardinality_Sat}]
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
        
    


def compute_election_properties(election_parser: LazyElectionParser,
                                overwrite: bool = False,
                                verbosity: int = 1
                                ) -> None:
    election_obj = election_parser.get_election_obj()

    # we first compute the instance properties
    for instance_property in instance_property_mapping:
        metadata_obj = ElectionMetadata.objects.get(short_name=instance_property)
        if metadata_obj.applies_to_election(election_obj):
            unique_filters = {'election': election_obj,
                              'metadata': metadata_obj}
            if overwrite or not exists_in_database(ElectionDataProperty, **unique_filters):
                instance, profile = election_parser.get_parsed_election()
                ElectionDataProperty.objects.update_or_create(**unique_filters,
                                                              defaults={"value": instance_property_mapping[instance_property](instance)}) 

    # we now compute the profile properties
    for profile_property in profile_property_mapping:
        metadata_obj = ElectionMetadata.objects.get(short_name=profile_property)
        if metadata_obj.applies_to_election(election_obj):
            unique_filters = {'election': election_obj,
                              'metadata': metadata_obj}
            if overwrite or not exists_in_database(ElectionDataProperty, **unique_filters):
                instance, profile = election_parser.get_parsed_election()
                ElectionDataProperty.objects.update_or_create(**unique_filters,
                                                              defaults={"value": profile_property_mapping[profile_property](instance, profile)}) 


def compute_election_results(election_parser: LazyElectionParser,
                             rule_list: Iterable[str] | None,
                             overwrite: bool = False,
                             verbosity: int = 1
                             ) -> None:
    election_obj = election_parser.get_election_obj()

    rules = rule_mapping(election_obj.budget)
    for rule in rules:
        if rule_list == None or rule in rule_list:
            rule_obj = Rule.objects.get(abbreviation=rule)
            if (rule_obj.applies_to_election(election_obj)):
                unique_filters = {'election': election_obj,
                                  'rule': rule_obj}
                if overwrite or not exists_in_database(RuleResult, **unique_filters):
                    print_if_verbose("Computing {}.".format(rule), 2, verbosity)
                    rule_result_obj, _ = RuleResult.objects.update_or_create(**unique_filters)
                    instance, profile = election_parser.get_parsed_election()
                    pabutools_result = rules[rule]['func'](
                        instance,
                        profile,
                        **rules[rule]['params']
                    )
                    rule_result_obj.selected_projects.set(
                        [Project.objects.get(election=election_obj, project_id=project.name) for project in pabutools_result]
                    )


def compute_rule_result_properties(election_parser: LazyElectionParser,
                                   rule_property_list: Iterable[str] | None,
                                   overwrite: bool = False,
                                   verbosity: int = 1
                                   ) -> None:
    election_obj = election_parser.get_election_obj()

    for rule_result_object in RuleResult.objects.filter(election=election_obj):
        print_if_verbose("Computing properties for {} results.".format(rule_result_object.rule.abbreviation), 2, verbosity)
        budget_allocation = [project_object_to_pabutools(project) for project in rule_result_object.selected_projects.all()]

        for property in satisfaction_property_mapping:
            if rule_property_list == None or property in rule_property_list:
                metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                if metadata_obj.applies_to_election(election_obj):
                    unique_filters = {'rule_result': rule_result_object,
                                      'metadata': metadata_obj}
                    if overwrite or not exists_in_database(RuleResultDataProperty, **unique_filters):
                        print_if_verbose("Computing {}.".format(property), 3, verbosity)
                        instance, profile = election_parser.get_parsed_election()
                        value = votersatisfaction.avg_satisfaction(
                            instance,
                            profile,
                            budget_allocation,
                            satisfaction_property_mapping[property]['sat_class']
                        )
                        normalizer = 1
                        if satisfaction_property_mapping[property]['normalizer_func'] != None:
                            normalizer = satisfaction_property_mapping[property]['normalizer_func'](instance, instance.budget_limit)
                            
                        RuleResultDataProperty.objects.update_or_create(**unique_filters,
                                                                        defaults={"value": str(float(value/normalizer))}) 

        for property in gini_property_mapping:
            if rule_property_list == None or property in rule_property_list:
                metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                if metadata_obj.applies_to_election(election_obj):
                    unique_filters = {'rule_result': rule_result_object,
                                      'metadata': metadata_obj}
                    if overwrite or not exists_in_database(RuleResultDataProperty, **unique_filters):
                        print_if_verbose("Computing {}.".format(property), 3, verbosity)
                        instance, profile = election_parser.get_parsed_election()
                        value = votersatisfaction.gini_coefficient_of_satisfaction(
                            instance,
                            profile,
                            budget_allocation,
                            gini_property_mapping[property],
                            invert=True
                        )
                        RuleResultDataProperty.objects.update_or_create(**unique_filters,
                                                                        defaults={"value": str(float(value))})

        property = "category_prop"
        if rule_property_list == None or property in rule_property_list:
            metadata_obj = RuleResultMetadata.objects.get(short_name=property)
            if metadata_obj.applies_to_election(election_obj) and election_obj.has_categories:
                unique_filters = {'rule_result': rule_result_object,
                                  'metadata': metadata_obj}
                if overwrite or not exists_in_database(RuleResultDataProperty, **unique_filters):
                    print_if_verbose("Computing {}.".format(property), 3, verbosity)
                    instance, profile = election_parser.get_parsed_election()
                    value = category.category_proportionality(
                        instance,
                        profile,
                        budget_allocation
                    )
                    RuleResultDataProperty.objects.update_or_create(**unique_filters,
                                                                    defaults={"value": str(float(value))}) 
    
        if len(budget_allocation) > 0:
            property = "med_select_cost"
            if rule_property_list == None or property in rule_property_list:
                metadata_obj = RuleResultMetadata.objects.get(short_name=property)
                if metadata_obj.applies_to_election(election_obj):
                    unique_filters = {'rule_result': rule_result_object,
                                      'metadata': metadata_obj}
                    if overwrite or not exists_in_database(RuleResultDataProperty, **unique_filters):
                        print_if_verbose("Computing {}.".format(property), 3, verbosity)
                        value = instanceproperties.median_project_cost(budget_allocation)
                        RuleResultDataProperty.objects.update_or_create(**unique_filters,
                                                                        defaults={"value": str(float(value))}) 

        property = "agg_nrmcost_sat"
        if rule_property_list == None or property in rule_property_list:    
            metadata_obj = RuleResultMetadata.objects.get(short_name=property)
            if metadata_obj.applies_to_election(election_obj):
                unique_filters = {'rule_result': rule_result_object,
                                  'metadata': metadata_obj}
                if overwrite or not exists_in_database(RuleResultDataProperty, **unique_filters):
                    print_if_verbose("Computing {}.".format(property), 3, verbosity)
                    instance, profile = election_parser.get_parsed_election()
                    value = satisfaction_histogram(
                        instance,
                        profile,
                        budget_allocation,
                        Cost_Sat,
                        max_satisfaction=max_budget_allocation_cost(instance, instance.budget_limit),
                        num_bins=21
                    )
                    RuleResultDataProperty.objects.update_or_create(**unique_filters,
                                                                    defaults={"value": json.dumps(value)})



def compute_properties(election_names=None,
                       rules=None,
                       rule_properties=False,
                       exact=False,
                       overwrite: bool = False,
                       verbosity=1):
    election_query = Election.objects.all()
    if election_names != None:
        election_query = election_query.filter(name__in=election_names)
    if not exact:
        fractions.FRACTION = 'float'
    n_elections = len(election_query)
    for index, election_obj in enumerate(election_query):
        print_if_verbose("Computing properties of election {}/{}: {}".format(index+1, n_elections, election_obj.name), 1, verbosity, persist=True)
        election_parser = LazyElectionParser(election_obj, verbosity)
        
        print_if_verbose("basic election properties...", 1, verbosity)
        compute_election_properties(election_parser, overwrite=overwrite, verbosity=verbosity)

        if rules == None or len(rules) > 0:
            print_if_verbose("rule results...", 1, verbosity)
            compute_election_results(election_parser, rules, overwrite=overwrite, verbosity=verbosity)
        
        if rule_properties == None or len(rule_properties) > 0:
            print_if_verbose("rule result properties...", 1, verbosity)
            compute_rule_result_properties(election_parser, rule_properties, overwrite=overwrite, verbosity=verbosity)

class Command(BaseCommand):
    help = "compute all properties, rules and rule result properties for the elections in the database"
    
    def add_arguments(self, parser):
        parser.add_argument('-e','--election_names', nargs='*', type=str, default=None,
                            help="Give a list of election names for which you want to compute properties.")
        parser.add_argument('-r', '--rules', nargs='*', type=str, default=None,
                            help="Give a list of rules for which you want to the results. Discard option to compute all rules, no parameter to skip the rule computation.")
        parser.add_argument('-p', '--rule_properties', nargs='*', type=str, default=None,
                            help="Give a list of rule properties which you want to compute. Discard option to compute all properties, no parameter to skip the property computation")
        parser.add_argument('--exact', nargs='?', type=bool, const=True, default=False,
                            help="Use exact fractions instead of floats for computing results.")
        parser.add_argument('-o', '--overwrite', nargs='?', type=bool, const=True, default=False,
                            help="Overwrite properties that were already computed.")
        # parser.add_argument('-o', '--overwrite', nargs='?', type=bool, const=True, default=False)
    
    def handle(self, *args, **options):
        compute_properties(election_names=options['election_names'],
                           rules=options['rules'],
                           rule_properties=options['rule_properties'],
                           exact=options['exact'],
                           overwrite=options['overwrite'],
                           verbosity=options["verbosity"])