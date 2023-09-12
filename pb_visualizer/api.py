from collections.abc import Callable, Iterable
import datetime
from email.policy import default
import json
import math
from time import sleep

import numpy as np

from .models import  Rule
from .serializers import *

from collections import defaultdict
from django.core import serializers
from django.db import models
from django.db.models import F, Q, Avg, Sum, Case, When, FloatField, BooleanField, QuerySet, Min, Max, Count, ExpressionWrapper, Value
from django.db.models.functions import Cast, Floor, Ln
from django.core.exceptions import FieldDoesNotExist 

from pb_visualizer.pabutools import election_object_to_pabutools, project_object_to_pabutools
from pabutools.election.satisfaction import SatisfactionProfile, Relative_Cost_Approx_Normaliser_Sat



def _get_type_from_model_field(field):
    field_type = type(field)
    if field_type == models.IntegerField:
        return 'int'
    elif field_type == models.DecimalField:
        return 'float'
    elif field_type == models.DateField:
        return 'date'
    elif field_type == models.BooleanField:
        return 'bool'
    elif (   field_type == models.CharField
          or field_type == models.TextField
          or field_type == models.ManyToManyRel
          or field_type == models.ForeignKey):
        return 'str'
    else:
        return 'not supported'


def get_ballot_type_list() -> list[dict]:
    ballot_type_query = BallotType.objects.all()
    ballot_type_query = ballot_type_query.annotate(num_elections=Count("elections")).order_by('order_priority')
    ballot_type_query = ballot_type_query.filter(num_elections__gt=0)
    ballot_type_serializer = BallotTypeSerializer(ballot_type_query, many=True)

    return {'data': ballot_type_serializer.data}


def get_election_list(filters: dict) -> list[dict]:
    election_query_set = filter_elections(**filters)
    election_serializer = ElectionSerializerFull(election_query_set, many=True)

    ballot_type_query = BallotType.objects.all().filter(elections__in=election_query_set).distinct()
    ballot_type_serializer = BallotTypeSerializer(ballot_type_query, many=True)
    
    return {'data': election_serializer.data, 'metadata': {'ballot_types': ballot_type_serializer.data}}


def get_election_details(property_short_names, ballot_type: str, filters: dict) -> list[dict]:
    election_query_set = filter_elections(**filters)
    election_details_collection = {}
    
    properties = get_filterable_election_property_list(
        property_short_names=property_short_names,
        ballot_type=ballot_type
    )['data']

    for election_obj in election_query_set:    
        election_dict = ElectionSerializer(election_obj).data

        election_details = {}

        # first we get all the properties that are fields of the election model
        for property in properties:
            if property['short_name'] in Election.public_fields:
                election_details[property['short_name']] = election_dict[property['short_name']]
        
        # then we get all the properties that are ElectionMetadata
        data_props_query = ElectionDataProperty.objects.all().filter(
            election=election_obj,
            metadata__short_name__in = [p['short_name'] for p in properties],
        )
        for data_prop_obj in data_props_query:
            election_details[data_prop_obj.metadata.short_name] = data_prop_obj.value

        
        election_details_collection[election_obj.id] = election_details

    return {'data': election_details_collection, 'metadata': properties}


def get_project_list(election_id: int) -> list[dict]:
    project_query_set = Project.objects.all().filter(election__id=election_id)
    project_serializer = ProjectSerializer(project_query_set, many=True)

    rule_query_set = Rule.objects.all().filter(rule_results__election__id=election_id)
    rule_serializer = RuleSerializer(rule_query_set, many=True)

    return {'data': project_serializer.data, 'metadata': {'rule_results_existing': rule_serializer.data}}


def get_rule_family_list(ballot_types: list[str] = None) -> list[dict]:
    rule_family_query = RuleFamily.objects.all().filter()
    rule_family_serializer = RuleFamilyFullSerializer(rule_family_query, many=True)

    return {'data': rule_family_serializer.data}


def get_rule_result_property_list(property_short_names: Iterable[str] = None) -> list[dict]:
    if property_short_names:
        try:
            query = RuleResultMetadata.objects.all().filter(short_name__in=property_short_names)
        except Exception as e:
            raise ValueError("Invalid property short name.")
    else:
        query = RuleResultMetadata.objects.all()
            
    serializer = RuleResultMetadataSerializer(query, many=True)
    return {'data': serializer.data}


def get_filterable_election_property_list(property_short_names: Iterable[str], ballot_type: str = None) -> list[dict]:
    
    def field_to_property_dict(property_short_name):
        try:
            property_field = Election._meta.get_field(property_short_name)
            
            return {
                'name': property_field.verbose_name,
                'short_name': property_short_name,
                'description': property_field.help_text,
                'inner_type': _get_type_from_model_field(property_field)
            }
        except FieldDoesNotExist:
            raise ValueError("Invalid property short name: {}.".format(property_short_name))
    
    
    properties = []
    if property_short_names != None:
        for property_short_name in property_short_names:
            if property_short_name in Election.public_fields:
                properties.append(field_to_property_dict(property_short_name))
            else:
                property_query = ElectionMetadata.objects.all().filter(short_name=property_short_name)
                if ballot_type != None:
                    property_query = property_query.filter(applies_to=ballot_type)
                if property_query.exists():
                    properties.append(ElectionMetadataSerializer(property_query.first()).data)
    else: 
        for field_name in Election.public_fields:
            properties.append(field_to_property_dict(field_name))

        property_query = ElectionMetadata.objects.all()
        if ballot_type != None:
            property_query = property_query.filter(applies_to=ballot_type)
        for metadata_obj in property_query:
            properties.append(ElectionMetadataSerializer(metadata_obj).data)
    return {'data': properties}




def get_rule_result_average_data_properties(rule_abbr_list: Iterable[str],
                                            property_short_names: Iterable[str],
                                            election_filters: dict = {}
                                            ) -> dict[str, dict[str, float]]:

    election_query_set = filter_elections(**election_filters)
    election_query_set = filter_elections_by_rule_properties(election_query_set,
                                                             rule_abbr_list=rule_abbr_list,
                                                             property_short_names=property_short_names)
    rule_result_data_property_query_set = RuleResultDataProperty.objects.all().filter(
        rule_result__election__in=election_query_set
    )

    data_dict = {}
    for rule in rule_abbr_list:
        data_dict[rule] = {}
        for prop_name in property_short_names:
            rule_result_metadata_obj = RuleResultMetadata.objects.get(short_name=prop_name)
            if rule_result_metadata_obj.inner_type == "float" or rule_result_metadata_obj.inner_type == "int" :
                data_dict[rule][prop_name] = rule_result_data_property_query_set.filter(
                        rule_result__rule__abbreviation=rule,
                        metadata__short_name=prop_name
                ).annotate(value_as_float=Cast('value', FloatField())
                ).aggregate(Avg('value_as_float'))['value_as_float__avg']
                
            elif rule_result_metadata_obj.inner_type == "list[float]":
                prop_list = []
                for rule_result_data_property in rule_result_data_property_query_set.filter(rule_result__rule__abbreviation=rule,
                                                                                            metadata__short_name=prop_name).all():
                    prop_list.append(json.loads(rule_result_data_property.value))

                if len(prop_list) > 0:
                    avg_props = [0 for i in range(len(prop_list[0]))]
                    for prop in prop_list:
                        for i in range(len(prop)):
                            avg_props[i] += prop[i]
                    for i in range(len(avg_props)):
                            avg_props[i] /= len(prop_list)
                    data_dict[rule][prop_name] = avg_props
                else: 
                    data_dict[rule][prop_name] = []
    return {'data': data_dict, 'meta_data': {'num_elections': len(election_query_set)}}


def get_satisfaction_histogram(rule_abbr_list: Iterable[str],
                               election_filters: dict = {}
                               ) -> dict[str, list[float]]:
    data_dict = get_rule_result_average_data_properties(rule_abbr_list,
                                                        ['aggregated_norm_cost_satisfaction', 'avg_norm_cost_satisfaction'],
                                                        election_filters=election_filters)
    
    data_dict['data'] = {
        rule: {
            'hist_data': data_dict['data'][rule]['aggregated_norm_cost_satisfaction'],
            'avg': data_dict['data'][rule]['avg_norm_cost_satisfaction']
            }
        for rule in  data_dict['data']
    }
    return data_dict


def get_election_property_histogram(election_property_short_name: str,
                                    election_filters: dict = {},
                                    num_bins: int = 10,
                                    by_ballot_type: bool = False,
                                    log_scale: bool = False
                                    ) -> tuple[list, list]:
    
    ballot_type_names = [prop_tuple[0] for prop_tuple in BallotType.objects.all().values_list('name')]

    election_query_set = filter_elections(**election_filters)

    election_meta_data_obj = ElectionMetadata.objects.filter(short_name=election_property_short_name)
    if election_meta_data_obj.exists():
        election_data_property_query = ElectionDataProperty.objects.all().filter(
            metadata__short_name=election_property_short_name,
            election__in=election_query_set
        ).annotate(ballot_type=F('election__ballot_type__name'))

        hist_data = histogram_data_from_query_set_and_field(
            query_set=election_data_property_query,
            field_name='value',
            by_category={'field_name': 'election__ballot_type__name', 'categories': ballot_type_names} if by_ballot_type else None,
            num_bins=num_bins,
            log_scale=log_scale
        )
    else:
        hist_data = histogram_data_from_query_set_and_field(
            query_set=election_query_set,
            field_name=election_property_short_name,
            by_category={'field_name': 'ballot_type__name', 'categories': ballot_type_names} if by_ballot_type else None,
            num_bins=num_bins,
            log_scale=log_scale
        )

    election_property = get_filterable_election_property_list([election_property_short_name])['data'][0]
    return {
        'data': hist_data,
        'meta_data': {
            'election_property': election_property
        }
    }

     

def histogram_data_from_query_set_and_field(query_set: QuerySet,
                                            field_name: str,
                                            num_bins: int,
                                            by_category: dict = None,
                                            log_scale: bool = False
                                            ) -> tuple[list, list]:
    
    if by_category:
        query_sets_by_category = {category: query_set.filter(**{by_category['field_name']: category})
                                                                for category in by_category['categories']}

    min_value = float(query_set.aggregate(Min(field_name))[field_name + '__min'])
    max_value = float(query_set.aggregate(Max(field_name))[field_name + '__max'])

    if min_value == max_value:
        if by_category:
            values = {category: [query_sets_by_category[category].count()] for category in by_category['categories']}
        else:
            values = [query_set.count()]
        return {
            'bins': [min_value, min_value],
            'values': values
        }
    
    if min_value <= 0 and log_scale:
        raise ValueError("log_scale option is only possible if all values are > 0")

    if(log_scale):
        bins = [min_value * (max_value/min_value)**(float(i)/num_bins) for i in range(num_bins+1)]
        bin_midpoints = [min_value * (max_value/min_value)**(float(i+0.5)/num_bins) for i in range(num_bins)]
        annotation_formula = Floor(Ln(Cast(field_name, FloatField())/min_value)/Ln(max_value/min_value)*num_bins)
    else:
        bins = [min_value + i*(max_value-min_value)/num_bins for i in range(num_bins+1)]
        bin_midpoints = [min_value + (i+0.5)*(max_value-min_value)/num_bins for i in range(num_bins)]
        annotation_formula = Floor((Cast(field_name, FloatField())-min_value)/(max_value-min_value)*num_bins)


    counters = {str(i): Count('id', filter=Q(hist_bin=i)) for i in range(num_bins-1)}
    counters[str(num_bins-1)] = Count('id', filter=Q(hist_bin__in=[num_bins-1, num_bins])) # last bin should be closed interval
    
    if by_category:
        for category in by_category['categories']:
            query_sets_by_category[category] = query_sets_by_category[category].annotate(hist_bin=annotation_formula)

        histogram_data_values = {
            category: list(query_sets_by_category[category].aggregate(**counters).values())
                                                    for category in by_category['categories']
        }
    else:
        query_set = query_set.annotate(hist_bin=annotation_formula)
        histogram_data_values = list(query_set.aggregate(**counters).values())

    histogram_data = {
        'bins': bins,
        'bin_midpoints': bin_midpoints,
        'values': histogram_data_values
    }

    return histogram_data


# could be optimized (looping through categories probably not necessary)
def category_proportions(election_id: int,
                         rule_abbreviation_list: str):
    try:
        election_obj = Election.objects.all().get(id=election_id)
    except:
        raise ValueError("Invalid election id.")
    
    if election_obj.has_categories:

        categories_query = Category.objects.all().filter(election=election_obj)
        votes = PreferenceInfo.objects.all().filter(voter__election=election_obj)    

        category_names = []
        vote_cost_shares = []
        vote_cost_share_sum = 0 
        result_cost_shares = {rule_abbreviation: [] for rule_abbreviation in rule_abbreviation_list}
        result_cost_share_sums = {rule_abbreviation: 0 for rule_abbreviation in rule_abbreviation_list}
        for category_obj in categories_query:
            category_names.append(category_obj.name)
            
            vote_cost_share_formula = Sum(F('project__cost')*F('preference_strength'), output_field=FloatField(), default=0)
            vote_cost_share = votes.filter(project__categories=category_obj).aggregate(vote_cost_share=vote_cost_share_formula)
            vote_cost_shares.append(vote_cost_share['vote_cost_share'])
            vote_cost_share_sum += vote_cost_share['vote_cost_share']
            
            for rule_abbreviation in rule_abbreviation_list:
                projects_selected = Project.objects.all().filter(
                    election=election_obj,
                    rule_results_selected_by__rule__abbreviation=rule_abbreviation
                )
                result_cost_share_formula = Sum('cost', output_field=FloatField(), default=0)
                result_cost_share = projects_selected.filter(categories=category_obj).aggregate(result_cost_share=result_cost_share_formula)
                result_cost_shares[rule_abbreviation].append(result_cost_share['result_cost_share'])
                result_cost_share_sums[rule_abbreviation] += result_cost_share['result_cost_share']
        
        if vote_cost_share_sum == 0:
            raise ValueError("Election does not have votes for projects with positive cost and categories.")

        # if a rule does not select any projects with positive cost and categories:
        # set the divider to 1 to avoid dividing by 0, all values will be zero for that rule 
        for rule_abbreviation in rule_abbreviation_list:
            if result_cost_share_sums[rule_abbreviation] == 0:
                result_cost_share_sums[rule_abbreviation] = 1

        for i in range(len(category_names)):
            vote_cost_shares[i] /= vote_cost_share_sum
            for rule_abbreviation in rule_abbreviation_list:
                result_cost_shares[rule_abbreviation][i] /= result_cost_share_sums[rule_abbreviation]
    else:
        category_names, vote_cost_shares = [], []
        result_cost_shares  = {rule_abbreviation: [] for rule_abbreviation in rule_abbreviation_list}
    return {
        'category_names': category_names,
        'vote_cost_shares': vote_cost_shares,
        'result_cost_shares': result_cost_shares,
    }


def filter_elections(election_query_set: QuerySet | None = None,
                     **election_filters
                     ) -> QuerySet:
            
    if election_query_set == None:
        election_query_set = Election.objects.all()

    for election_property in election_filters:
        if election_property == "id_list":
            election_query_set = election_query_set.filter(id__in=election_filters[election_property])
        elif election_property == "ballot_types":
            election_query_set = election_query_set.filter(ballot_type__in=election_filters[election_property])
        elif election_property in Election.public_fields:
            type = _get_type_from_model_field(Election._meta.get_field(election_property))
            if type == 'int' or type == 'float':
                if 'min' in election_filters[election_property] and election_filters[election_property]['min'] != None:
                    election_query_set = election_query_set.filter(
                        **{election_property+"__gte": election_filters[election_property]['min']}
                    )
                if 'max' in election_filters[election_property] and election_filters[election_property]['max'] != None:
                    election_query_set = election_query_set.filter(
                        **{election_property+"__lte": election_filters[election_property]['max']}
                    )
            elif type == 'date':
                if 'min' in election_filters[election_property] and election_filters[election_property]['min'] != None:
                    election_query_set = election_query_set.filter(
                        **{election_property+"__gte": datetime.date(election_filters[election_property]['min'])}
                    )
                if 'max' in election_filters[election_property] and election_filters[election_property]['max'] != None:
                    election_query_set = election_query_set.filter(
                        **{election_property+"__lte": datetime.date(election_filters[election_property]['max'])}
                    )
            elif type == 'bool':
                if election_filters[election_property] != None:
                    election_query_set = election_query_set.filter(
                        **{election_property: election_filters[election_property]}
                    )
            else:
                # other types not yet supported, if you add a field of a different type, write a filter here, TODO: add str filter
                raise ValueError("Property type {} is not supported for filtering.".format(type))



        elif ElectionMetadata.objects.all().filter(short_name=election_property).exists():
            # no type check, because all meta properties are numbers
            if 'min' in election_filters[election_property] and election_filters[election_property]['min'] != None:
                election_query_set = election_query_set.filter(
                    data_properties__metadata__short_name=election_property,
                    data_properties__value__gte=election_filters[election_property]['min']
                )
            if 'max' in election_filters[election_property] and election_filters[election_property]['max'] != None:
                election_query_set = election_query_set.filter(
                    data_properties__metadata__short_name=election_property,
                    data_properties__value__lte=election_filters[election_property]['max']
                )
        else:
            # property does not exist or is not allowed to be filtered through the api
            raise ValueError("Property {} does not exist or is not supported for filtering.".format(election_property))

    return election_query_set


def filter_elections_by_rule_properties(election_query_set: QuerySet,
                                        rule_abbr_list: Iterable[str] = [],
                                        property_short_names: Iterable[str] = [],
                                        ) -> QuerySet:
    for rule in rule_abbr_list:
        rule_result_query_set = RuleResult.objects.all().filter(rule__abbreviation=rule)
        for prop in property_short_names:
            rule_result_query_set = rule_result_query_set.filter(
                Q(data_properties__metadata__short_name=prop)
            )
            
        election_query_set = election_query_set.filter(
            Q(rule_results__in=rule_result_query_set)
        )

    return election_query_set

