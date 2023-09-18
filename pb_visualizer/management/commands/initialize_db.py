from django.core.management.base import BaseCommand

from pb_visualizer.models import *



def initialize_ballot_types():
    ballot_type_objs = {}
    
    ballot_type_objs["approval"], _ = BallotType.objects.update_or_create(name="approval",
                                      defaults={
                                        "description": "approval ballots",
                                        "order_priority": 1})

    ballot_type_objs["ordinal"], _ = BallotType.objects.update_or_create(name="ordinal",
                                      defaults={
                                        "description": "ordinal ballots",
                                        "order_priority": 2})

    ballot_type_objs["cumulative"], _ = BallotType.objects.update_or_create(name="cumulative",
                                      defaults={
                                        "description": "cumulative ballots",
                                        "order_priority": 3})

    ballot_type_objs["cardinal"], _ = BallotType.objects.update_or_create(name="cardinal",
                                      defaults={
                                        "description": "cardinal ballots",
                                        "order_priority": 4})

    return(ballot_type_objs)


def initialize_election_metadata(ballot_type_objs):
    # election metadata for all vote types
    order_priority = 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="max_length",
        defaults={
            "name": "maximum allowed ballot length",
            "description": "maximum number of projects a voter can approve",
            "inner_type": "int",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"],
                                          ballot_type_objs["ordinal"],
                                          ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="min_length",
        defaults={
            "name": "minimum allowed ballot length",
            "description": "minimum number of projects a voter can approve",
            "inner_type": "int",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"],
                                          ballot_type_objs["ordinal"],
                                          ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    # election metadata for approval votes
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="max_sum_cost",
        defaults={
            "name": "maximum allowed ballot cost",
            "description": "maximum cost restriction on the ballots",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="min_sum_cost",
        defaults={
            "name": "minimum allowed ballot cost",
            "description": "minimum cost restriction on the ballots",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    # election metadata for cumulative votes     
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="max_sum_points",
        defaults={
            "name": "maximum allowed total points",
            "description": "upper restriction on the total points each voter can give",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="min_sum_points",
        defaults={
            "name": "minimum allowed total points",
            "description": "lower restriction on the total points each voter can give",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"]])
        
    # election metadata for cumulative and cardinal votes     
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="max_points",
        defaults={
            "name": "maximum allowed points",
            "description": "upper restriction on the number of points a voter can give to a single project",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])
        
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="min_points",
        defaults={
            "name": "minimum allowed points",
            "description": "lower restriction on the number of points a voter can give to a single project",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="default_score",
        defaults={
            "name": "default score",
            "description": "default score of a project in a ballot",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cardinal"]])




    # election analysis
    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="sum_proj_cost",
        defaults={
            "name": "total cost of all projects",
            "description": "total sum of the costs of all projects",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"],
                                          ballot_type_objs["ordinal"],
                                          ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="funding_scarcity",
        defaults={
            "name": "funding scarcity",
            "description": "funding scarcity is given as the ratio of the total project cost to the budget limit",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"],
                                          ballot_type_objs["ordinal"],
                                          ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_project_cost",
        defaults={
            "name": "average project cost",
            "description": "average cost of all the projects",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"],
                                          ballot_type_objs["ordinal"],
                                          ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="median_project_cost",
        defaults={
            "name": "median project cost",
            "description": "median cost of all the projects",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"],
                                          ballot_type_objs["ordinal"],
                                          ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="std_dev_project_cost",
        defaults={
            "name": "standard deviation of project costs",
            "description": "standard deviation of the cost of all the projects",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"],
                                          ballot_type_objs["ordinal"],
                                          ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_ballot_length",
        defaults={
            "name": "average ballot length",
            "description": "average length of all submitted ballots",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"],
                                          ballot_type_objs["ordinal"],
                                          ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="median_ballot_length",
        defaults={
            "name": "median ballot length",
            "description": "median length of all submitted ballots",
            "inner_type": "int",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"],
                                          ballot_type_objs["ordinal"],
                                          ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_ballot_cost",
        defaults={
            "name": "average ballot cost",
            "description": "average cost of all submitted ballots",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="median_ballot_cost",
        defaults={
            "name": "median ballot cost",
            "description": "median cost of all submitted ballots",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_approval_score",
        defaults={
            "name": "average approval score",
            "description": "average number of approvals over all the projects",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="median_approval_score",
        defaults={
            "name": "median approval score",
            "description": "median number of approvals over all the projects",
            "inner_type": "int",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["approval"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="avg_total_score",
        defaults={
            "name": "average total project score",
            "description": "average total score of all the projects",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])

    order_priority += 1
    election_metadata_obj, _ = ElectionMetadata.objects.update_or_create(
        short_name="median_total_score",
        defaults={
            "name": "median total project score",
            "description": "median total score of all the projects",
            "inner_type": "float",
            "order_priority": order_priority
        }
    )
    election_metadata_obj.applies_to.set([ballot_type_objs["cumulative"],
                                          ballot_type_objs["cardinal"]])


def initialize_rules(ballot_type_objs):

    #  rule families
    order_priority = 1
    greedy_obj, _ = RuleFamily.objects.update_or_create(
        abbreviation = "greedy",
        defaults={
            "name": "Greedy",
            "description": "Greedy rules",
            "order_priority": order_priority
        }
    )

    order_priority += 1
    max_sat_obj, _ = RuleFamily.objects.update_or_create(
        abbreviation = "max_sat",
        defaults={
            "name": "Satisfaction maximizer",
            "description": "Rules maximizing some satisfaction function",
            "order_priority": order_priority
        }
    )

    order_priority += 1
    mes_obj, _ = RuleFamily.objects.update_or_create(
        abbreviation = "mes",
        defaults={
            "name": "Method of equal shares",
            "description": "Method of equal shares and variations",
            "order_priority": order_priority
        }
    )

    order_priority += 1
    other_obj, _ = RuleFamily.objects.update_or_create(
        abbreviation = "other",
        defaults={
            "name": "Other",
            "description": "Other rules",
            "order_priority": order_priority
        }
    )


    # rules
    
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation = "greedy_card",
        defaults={
            "name": "Greedy (card)",
            "description": "Greedily choose the project with the best cost to approval ratio",
            "order_priority": order_priority,
            "rule_family": greedy_obj
        }
    )
    rule_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation = "greedy_cost",
        defaults={
            "name": "Greedy (cost)",
            "description": "Greedily choose the most approved projects",
            "order_priority": order_priority,
            "rule_family": greedy_obj
        }
    )
    rule_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation = "greedy_cc",
        defaults={
            "name": "Greedy (Chamberlin-Courant)",
            "description": "Greedily choose the project supported by the highest number of completely unsatisfied voters",
            "order_priority": order_priority,
            "rule_family": greedy_obj
        }
    )
    rule_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation = "max_card",
        defaults={
            "name": "Maximum cardinality satisfaction",
            "description": "Chooses the allocation yielding the maximum total cardinality satisfaction",
            "order_priority": order_priority,
            "rule_family": max_sat_obj
        }
    )
    rule_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation = "max_cost",
        defaults={
            "name": "Maximum cost satisfaction",
            "description": "Chooses the allocation yielding the maximum total cost satisfaction",
            "order_priority": order_priority,
            "rule_family": max_sat_obj
        }
    )
    rule_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation = "mes",
        defaults={
            "name": "Equal shares",
            "description": "The method of equal shares with budget increase and greedy (cost) completion",
            "order_priority": order_priority,
            "rule_family": mes_obj
        }
    )
    rule_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
    
    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation = "mes_uncompleted",
        defaults={
            "name": "Equal shares (no completion)",
            "description": "The method of equal shares without budget increase or completion",
            "order_priority": order_priority,
            "rule_family": mes_obj
        }
    )
    rule_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
    
    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation = "mes_greedy_app",
        defaults={
            "name": "Equal shares (greedy)",
            "description": "The method of equal shares with greedy approval completion",
            "order_priority": order_priority,
            "rule_family": mes_obj
        }
    )
    rule_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])

    order_priority += 1
    rule_obj, _ = Rule.objects.update_or_create(
        abbreviation = "seq_phragmen",
        defaults={
            "name": "Sequential Phragmen",
            "description": "Sequential Phragmen rule",
            "order_priority": order_priority,
            "rule_family": other_obj
        }
    )
    rule_obj.applies_to.set([ballot_type_objs["approval"]])
    

def initialize_rule_result_metadata(ballot_type_objs):
    
    order_priority = 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Average cardinality satisfaction",
        defaults={
            "description": "The average number of approved projects chosen by the rule over all voters.",
            "short_name": "avg_card_satisfaction",
            "inner_type": "float",
            "range": "0-",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
    
    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Average cardinality satisfaction (normalized)",
        defaults={
            "description": "The average number of approved projects chosen by the rule over all voters,"
                           "normalized by the maximum number of projects that could be chosen w.r.t. the budget limit.",
            "short_name": "avg_norm_card_satisfaction",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
    
    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Average relative cardinality satisfaction",
        defaults={
            "description": "The average relative number of approved project chosen by the rule over all voters.",
            "short_name": "avg_rel_card_satisfaction",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
    
    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Average cost satisfaction",
        defaults={
            "description": "The average cost satisfaction of the voters",
            "short_name": "avg_cost_satisfaction",
            "inner_type": "float",
            "range": "0-",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Average cost satisfaction (normalized)",
        defaults={
            "description": "The average cost satisfaction of the voters,"
                           "normalized by the maximum possible budget allocation cost (w.r.t. the budget limit)",
            "short_name": "avg_norm_cost_satisfaction",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Average relative cost satisfaction",
        defaults={
            "description": "The average relative cost satisfaction of the voters",
            "short_name": "avg_rel_cost_satisfaction",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
    
    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Category proportionality",
        defaults={
            "description": "",
            "short_name": "category_proportionality",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
    
    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Equality (inverted cost gini)",
        defaults={
            "description": "",
            "short_name": "equality",
            "inner_type": "float",
            "range": "01",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
    
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
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
    
    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Median selected cost",
        defaults={
            "description": "",
            "short_name": "median_selected_cost",
            "inner_type": "float",
            "range": "0-",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["ordinal"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])

    order_priority += 1
    metadata_obj, _ = RuleResultMetadata.objects.update_or_create(
        name="Aggregated normalized cost satisfaction distribution",
        defaults={
            "description": "The relative number of voters being x %% satisfied for x being 0, 0-5, 5-10, ..., 95-100.",
            "short_name": "aggregated_norm_cost_satisfaction",
            "inner_type": "list[float]",
            "range": "01",
            "order_priority": order_priority,
        }
    )
    metadata_obj.applies_to.set([
        ballot_type_objs["approval"],
        ballot_type_objs["cumulative"],
        ballot_type_objs["cardinal"]
    ])
        

def initialize_db():
    # initialize_tags()
    ballot_type_objs = initialize_ballot_types()
    initialize_election_metadata(ballot_type_objs)
    initialize_rules(ballot_type_objs)
    initialize_rule_result_metadata(ballot_type_objs)



class Command(BaseCommand):
    help = "Initializes the database, to be run once at the beginning"

    def handle(self, *args, **options):
        initialize_db()