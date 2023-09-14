from curses import meta
from importlib import metadata
import time
from django.test import TestCase
from pb_visualizer.management.commands.add_election import add_dataset
from pb_visualizer.management.commands.initialize_db import initialize_db
from pb_visualizer.models import *
from pb_visualizer.api import *
import os
from django.db.models import Q, Avg


# Create your tests here.
class TestApi(TestCase):
    def setUp(self):
        initialize_db()

    def test_election_filter(self):
        
        for i in range(3):
            election_obj = Election.objects.create(id=i,
                                                   name="e"+str(i),
                                                   budget=100*i,
                                                   ballot_type_id='approval',
                                                   num_votes=20*i,
                                                   num_projects=5*i)
            # project_obj1 = Project.objects.create(name="p1.1", cost=1, project_id="1", election_id=1)
            # project_obj2 = Project.objects.create(name="p1.2", cost=1, project_id="2", election_id=1)

            greedy_obj = Rule.objects.get(abbreviation = 'greedy_cost')
            mes_obj = Rule.objects.get(abbreviation = 'mes')
            
            # if i == 1:
            greedy_result_obj = RuleResult.objects.create(rule=greedy_obj, election=election_obj)
            mes_result_obj = RuleResult.objects.create(rule=mes_obj, election=election_obj)
            
            avg_cost_obj = RuleResultMetadata.objects.get(short_name='avg_cost_satisfaction')
            avg_card_obj = RuleResultMetadata.objects.get(short_name='avg_card_satisfaction')

            if i == 1:
                RuleResultDataProperty.objects.create(id=i*4+1, rule_result=greedy_result_obj, metadata=avg_cost_obj, value=str(i*4+1))
            RuleResultDataProperty.objects.create(id=i*4+2, rule_result=greedy_result_obj, metadata=avg_card_obj, value=str(i*4+2))
            RuleResultDataProperty.objects.create(id=i*4+3, rule_result=mes_result_obj, metadata=avg_cost_obj, value=str(i*4+3))
            RuleResultDataProperty.objects.create(id=i*4+4, rule_result=mes_result_obj, metadata=avg_card_obj, value=str(i*4+4))

            avg_ballot_length_obj = ElectionMetadata.objects.get(short_name="avg_ballot_length")
            ElectionDataProperty.objects.create(id=i, metadata=avg_ballot_length_obj, election=election_obj, value=float(i))

            avg_ballot_cost_obj = ElectionMetadata.objects.get(short_name="avg_ballot_cost")
            ElectionDataProperty.objects.create(id=i+10, metadata=avg_ballot_cost_obj, election=election_obj, value=float(i**2))
               
        election_query_set = Election.objects.all()
        election_query_set = filter_elections(election_query_set,
                                              num_votes={'min': 10},
                                              num_projects={'max': 8})
        
        assert(len(election_query_set) == 1)
        assert(election_query_set.first().name == "e1")
        
        election_query_set = Election.objects.all()
        election_query_set = filter_elections(election_query_set,
                                              num_votes={'max': 1000},
                                              num_projects={'min': 4},
                                              budget={'min': 200})
        assert(len(election_query_set) == 1)
        assert(election_query_set.first().name == "e2")

        election_query_set = Election.objects.all()
        election_query_set = filter_elections(election_query_set,
                                              budget={'max': 200})
        assert(len(election_query_set) == 3)

        election_query_set = Election.objects.all()
        election_query_set = filter_elections(election_query_set,
                                              ballot_types=['ordinal', 'approval'])
        assert(len(election_query_set) == 3)

        prop_list = ['avg_card_satisfaction', 'avg_cost_satisfaction']
        rule_list = ['mes', 'greedy_cost']

        election_query_set = Election.objects.all()
        election_query_set = filter_elections(election_query_set,
                                              avg_ballot_length={'min': 1})
        assert(len(election_query_set) == 2)
        election_query_set = filter_elections(election_query_set,
                                              avg_ballot_length={'max': 1})
        assert(len(election_query_set) == 1)
        assert(election_query_set.first().name == "e1")


        election_query_set = Election.objects.all()
        election_query_set = filter_elections_by_rule_properties(election_query_set,
                                                                 rule_abbr_list=rule_list,
                                                                 property_short_names=prop_list)

        assert(len(election_query_set) == 1)
        assert(election_query_set.first().name == "e1")

    def test_get_rule_result_average_data_properties(self):
        for i in range(2):
            election_obj = Election.objects.create(id=i, name="e"+str(i), budget=1, ballot_type_id='approval')

            greedy_obj = Rule.objects.get(abbreviation = 'greedy_cost')
            mes_obj = Rule.objects.get(abbreviation = 'mes')
            
            greedy_result_obj = RuleResult.objects.create(rule=greedy_obj, election=election_obj)
            mes_result_obj = RuleResult.objects.create(rule=mes_obj, election=election_obj)
                        
            avg_cost_obj = RuleResultMetadata.objects.get(short_name='avg_cost_satisfaction')
            avg_card_obj = RuleResultMetadata.objects.get(short_name='avg_card_satisfaction')

            RuleResultDataProperty.objects.create(id=i*4+1, rule_result=greedy_result_obj, metadata=avg_cost_obj, value=str(i*4+1))
            RuleResultDataProperty.objects.create(id=i*4+2, rule_result=greedy_result_obj, metadata=avg_card_obj, value=str(i*4+2))
            RuleResultDataProperty.objects.create(id=i*4+3, rule_result=mes_result_obj, metadata=avg_cost_obj, value=str(i*4+3))
            RuleResultDataProperty.objects.create(id=i*4+4, rule_result=mes_result_obj, metadata=avg_card_obj, value=str(i*4+4))


        prop_list = ['avg_card_satisfaction', 'avg_cost_satisfaction']
        rule_list = ['mes', 'greedy_cost']

        avg_values = get_rule_result_average_data_properties(rule_list, prop_list)
        
        assert(avg_values['data'] == {
            'greedy_cost': {'avg_card_satisfaction': 4, 'avg_cost_satisfaction': 3},
            'mes':    {'avg_card_satisfaction': 6, 'avg_cost_satisfaction': 5},
        })
        assert(avg_values['meta_data']['num_elections'] == 2)


    def test_get_satisfaction_histogram(self):

        for i in range(2):
            election_obj = Election.objects.create(id=i, name="e"+str(i), budget=1, ballot_type_id='approval')

            greedy_obj = Rule.objects.get(abbreviation = 'greedy_cost')
            mes_obj = Rule.objects.get(abbreviation = 'mes')
            
            greedy_result_obj = RuleResult.objects.create(rule=greedy_obj, election=election_obj)
            mes_result_obj = RuleResult.objects.create(rule=mes_obj, election=election_obj)
                        
            aggr_sat_obj = RuleResultMetadata.objects.get(short_name='aggregated_norm_cost_satisfaction')
            avg_sat_obj = RuleResultMetadata.objects.get(short_name='avg_norm_cost_satisfaction')

            if i == 0:
                RuleResultDataProperty.objects.create(id=1, rule_result=greedy_result_obj, metadata=aggr_sat_obj, value=json.dumps([.5, .5, 0]))
                RuleResultDataProperty.objects.create(id=2, rule_result=mes_result_obj, metadata=aggr_sat_obj, value=json.dumps([.75, .25, 0]))
                RuleResultDataProperty.objects.create(id=3, rule_result=greedy_result_obj, metadata=avg_sat_obj, value=.5)
                RuleResultDataProperty.objects.create(id=4, rule_result=mes_result_obj, metadata=avg_sat_obj, value=.5)
            else:
                RuleResultDataProperty.objects.create(id=5, rule_result=greedy_result_obj, metadata=aggr_sat_obj, value=json.dumps([0, 0, 1]))
                RuleResultDataProperty.objects.create(id=6, rule_result=mes_result_obj, metadata=aggr_sat_obj, value=json.dumps([.25, .25, .5]))
                RuleResultDataProperty.objects.create(id=7, rule_result=greedy_result_obj, metadata=avg_sat_obj, value=.5)
                RuleResultDataProperty.objects.create(id=8, rule_result=mes_result_obj, metadata=avg_sat_obj, value=.5)

        rule_list = ['mes', 'greedy_cost']
        hist_data = get_satisfaction_histogram(rule_list)

        assert(np.all(hist_data['data']['greedy_cost']['hist_data'] == [0.25, 0.25, 0.5]))
        assert(np.all(hist_data['data']['mes']['hist_data'] == [0.5, 0.25, 0.25]))
        assert(hist_data['meta_data']['num_elections'] == 2)


    def test_get_election_property_histogram(self):
        for i in range(4):
            election_obj = Election.objects.create(id=i, budget=10**i, num_votes=i, ballot_type_id=('approval' if i < 2 else 'ordinal'))
            avg_ballot_length_obj = ElectionMetadata.objects.get(short_name='avg_ballot_length')
            ElectionDataProperty.objects.create(id=i, election=election_obj, metadata=avg_ballot_length_obj, value=i**2-i)
                    
        hist_data = get_election_property_histogram('avg_ballot_length', num_bins=4, log_scale=False)

        assert(hist_data['data']['bins'] == [0, 1.5, 3, 4.5, 6])
        assert(hist_data['data']['bin_midpoints'] == [0.75, 2.25, 3.75, 5.25])
        assert(hist_data['data']['values'] == [2, 1, 0, 1])

        hist_data = get_election_property_histogram('avg_ballot_length', num_bins=4, log_scale=False, election_filters={'budget': {'min': 11}})

        assert(hist_data['data']['bins'] == [2, 3, 4, 5, 6])
        assert(hist_data['data']['values'] == [1, 0, 0, 1])

        hist_data = get_election_property_histogram('budget', num_bins=3, log_scale=True)

        assert(len(hist_data['data']['bins']) == 4)
        for i in range(4):
            assert(hist_data['data']['bins'][i] - 10**i < 0.00001)
        assert(len(hist_data['data']['bin_midpoints']) == 3)
        for i in range(3):
            assert(hist_data['data']['bin_midpoints'][i] - 10**i*3.16227766017 < 0.00001)
        assert(hist_data['data']['values'] == [1, 1, 2])

        hist_data = get_election_property_histogram('avg_ballot_length', num_bins=4, by_ballot_type=True, log_scale=False)
        
        assert(hist_data['data']['bins'] == [0, 1.5, 3, 4.5, 6])
        assert(hist_data['data']['bin_midpoints'] == [0.75, 2.25, 3.75, 5.25])
        
        assert(hist_data['data']['values']['approval'] == [2, 0, 0, 0])
        assert(hist_data['data']['values']['ordinal'] == [0, 1, 0, 1])
        assert(hist_data['data']['values']['cumulative'] == [0, 0, 0, 0])
        assert(hist_data['data']['values']['cardinal'] == [0, 0, 0, 0])

        hist_data = get_election_property_histogram('num_votes', num_bins=3, by_ballot_type=True, log_scale=False)
        assert(hist_data['data']['bins'] == [0, 1, 2, 3])
        assert(hist_data['data']['bin_midpoints'] == [0.5, 1.5, 2.5])
        
        assert(hist_data['data']['values']['approval'] == [1, 1, 0])
        assert(hist_data['data']['values']['ordinal'] == [0, 0, 2])
        assert(hist_data['data']['values']['cumulative'] == [0, 0, 0])
        assert(hist_data['data']['values']['cardinal'] == [0, 0, 0])


    def test_proportionality(self):
        election_obj = Election.objects.create(id=0,
                                               budget=10,
                                               num_votes=10,
                                               ballot_type_id='approval',
                                               has_categories=True)
        category_objs = []
        # target_objs = []
        for i in range(2):
            category_obj = Category.objects.create(name=i, election=election_obj)
            category_objs.append(category_obj)
            # target_obj = Target.objects.create(name=i, election=election_obj)
            # target_objs.append(target_obj)
        project_objs = []
        for i in range(4):
            project_obj = Project.objects.create(project_id=i, cost=4-i, election=election_obj)
            project_objs.append(project_obj)
            if i == 0:
                project_obj.categories.set(category_objs[0:1])
                # project_obj.targets.set(target_objs[0:1])
            elif i == 1:
                project_obj.categories.set(category_objs[0:2])
                # project_obj.targets.set(target_objs[1:2])
            else:
                project_obj.categories.set(category_objs[1:2])
                # project_obj.targets.set(target_objs[0:2])
        for i in range(4):
            voter_obj = Voter.objects.create(voter_id=i, election=election_obj)
            PreferenceInfo.objects.create(voter=voter_obj, project=project_objs[i])

        rule1_obj = Rule.objects.create(name='rule1', abbreviation='rule1')
        rule2_obj = Rule.objects.create(name='rule2', abbreviation='rule2')
        rule3_obj = Rule.objects.create(name='rule3', abbreviation='rule3')
        rule1_result_obj = RuleResult.objects.create(election=election_obj, rule=rule1_obj)
        rule2_result_obj = RuleResult.objects.create(election=election_obj, rule=rule2_obj)
        rule3_result_obj = RuleResult.objects.create(election=election_obj, rule=rule3_obj)
        rule1_result_obj.selected_projects.set(project_objs[0:3])
        rule2_result_obj.selected_projects.set(project_objs[2:4])
        rule3_result_obj.selected_projects.set([])
                    
        
        proportionality_data = category_proportions(election_id=0,
                                                    rule_abbreviation_list=['rule1', 'rule2', 'rule3'])
        
        assert(proportionality_data['category_names'] == ['0', '1'])
        assert(proportionality_data['vote_cost_shares'] == [7./13., 6./13.])
        assert(proportionality_data['result_cost_shares']['rule1'] == [7./12., 5./12.])
        assert(proportionality_data['result_cost_shares']['rule2'] == [0, 1])
        assert(proportionality_data['result_cost_shares']['rule3'] == [0, 0])

        self.assertRaises(ValueError, lambda: category_proportions(election_id=8,
                                                                   rule_abbreviation_list=['rule1', 'rule2', 'rule3']))
        
        election_obj = Election.objects.create(id=1,
                                               budget=10,
                                               ballot_type_id='approval',
                                               has_categories=True)

        self.assertRaises(ValueError, lambda: category_proportions(election_id=1,
                                                                   rule_abbreviation_list=['rule1', 'rule2', 'rule3']))
        
        election_obj = Election.objects.create(id=2,
                                               budget=10,
                                               ballot_type_id='approval',
                                               has_categories=False)

        proportionality_data = category_proportions(election_id=2,
                                                    rule_abbreviation_list=['rule1', 'rule2', 'rule3'])
        assert(proportionality_data['category_names'] == [])
        assert(proportionality_data['vote_cost_shares'] == [])
        assert(proportionality_data['result_cost_shares']['rule1'] == [])
        assert(proportionality_data['result_cost_shares']['rule2'] == [])
        assert(proportionality_data['result_cost_shares']['rule3'] == [])