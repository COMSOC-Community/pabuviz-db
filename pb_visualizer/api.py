from collections.abc import Iterable
import datetime
import json
import random
from django.core.files.storage import FileSystemStorage
from pb_visualizer.management.commands.add_election import add_election
from pb_visualizer.management.commands.compute_election_properties import compute_election_properties
from pb_visualizer.management.commands.compute_rule_result_properties import compute_rule_result_properties
from pb_visualizer.management.commands.compute_rule_results import compute_rule_results
from pb_visualizer.management.commands.remove_old_user_elections import remove_old_user_elections


from .models import Rule
from .serializers import *

from django.db import models
from django.db.models import (
    F,
    Q,
    Avg,
    Sum,
    FloatField,
    QuerySet,
    Min,
    Max,
    Count,
)
from django.db.models.functions import Cast, Floor, Ln

from rest_framework import status
from pb_visualizer.management.commands.utils import ApiExcepetion

import logging
logger = logging.getLogger('django')




def _get_type_from_model_field(field):
    """
    Maps a django Field to a type string. The strings used match the ones used
    with the inner_type model field on several models in the db.
    """
    field_type = type(field)
    if field_type == models.IntegerField:
        return "int"
    elif field_type == models.DecimalField:
        return "float"
    elif field_type == models.DateField:
        return "date"
    elif field_type == models.BooleanField:
        return "bool"
    elif field_type == models.CharField or field_type == models.TextField:
        return "str"
    elif field_type == models.ForeignKey:
        return "reference"
    else:
        return "not supported"


def get_ballot_type_list(filter_existing: bool = True, database: str = "default") -> dict[str,list[dict]]:
    """
    Returns a serialized list of ballot types.

    Parameters
    ----------
        filter_existing: bool,
            if True, then only ballot types with an election in the db are returned
        database: string
            name of the database to work on
    
    Returns
    -------
        dict
            "data": serialized list of ballot types
    """
    ballot_type_query = BallotType.objects.using(database).all()
    
    if filter_existing:
        ballot_type_query = ballot_type_query.annotate(
            num_elections=Count("elections")
        ).order_by("order_priority")
        ballot_type_query = ballot_type_query.filter(num_elections__gt=0)
    
    ballot_type_serializer = BallotTypeSerializer(ballot_type_query, many=True)
    return {"data": ballot_type_serializer.data}


def get_election_list(filters: dict[str], database: str = "default") -> dict[str,list[dict]]:
    """
    Returns a serialized list of all elections satisfying the filters in the database.

    Parameters
    ----------
        filters: dict
            filters to filter the elections by,
            for the format check filter_elections method.
        database: string
            name of the database to work on
    
    Returns
    -------
        dict
            "data":
                serialized list of elections
            "metadata":
                serialized list of all ballot types of these elections
    """
    election_query_set = filter_elections(**filters, database=database)
    election_serializer = ElectionSerializer(election_query_set, many=True)

    ballot_type_query = (
        BallotType.objects.using(database).all().filter(elections__in=election_query_set).distinct()
    )
    ballot_type_serializer = BallotTypeSerializer(ballot_type_query, many=True)

    return {
        "data": election_serializer.data,
        "metadata": {"ballot_types": ballot_type_serializer.data},
    }


def get_election_details(
    property_short_names: list[str],
    ballot_type: str,
    filters: dict,
    database: str = "default"
) -> dict[str, list[dict]]:
    """
    Returns a serialized list of all elections of the given ballot type satisfying the filters in the database.
    Additionally all election properties in property_short_names are injected into each election dictionary.

    Parameters
    ----------
        property_short_names: list[str]
            List of election property short names that should be included in the data.
            To request all possible values, use get_filterable_election_property_list.
        ballot_type: str,
            the ballot type of the elections requested
        filters: dict
            filters to filter the elections by,
            for the format check filter_elections method.
        database: string
            name of the database to work on
    
    Returns
    -------
        dict
            "data":
                list of elections dictionaries
                with all given property short names as keys and their values as values
            "metadata":
                serialized list of all given election properties
    """
    election_query_set = filter_elections(**filters, database=database)
    election_details_collection = {}

    properties = get_filterable_election_property_list(
        property_short_names=property_short_names,
        ballot_type=ballot_type,
        database=database
    )

    for election_obj in election_query_set:
        election_dict = ElectionSerializer(election_obj).data
        election_details = {}

        # first we get all the properties that are fields of the election model
        for property in properties["data"]:
            if property["short_name"] in Election.public_fields:
                election_details[property["short_name"]] = election_dict[
                    property["short_name"]
                ]

        # then we get all the properties that are ElectionMetadata
        data_props_query = ElectionDataProperty.objects.using(database).all().filter(
            election=election_obj,
            metadata__short_name__in=[p["short_name"] for p in properties["data"]],
        )
        for data_prop_obj in data_props_query:
            election_details[data_prop_obj.metadata.short_name] = data_prop_obj.value

        election_details["user_submitted"] = (database == "user_submitted")

        election_details_collection[election_obj.name] = election_details

    # TODO: also send metadata of properties or remove properties
    return {"data": election_details_collection, "metadata": properties["data"]} 


def get_project_list(
    election_name: str,
    database: str = "default"
) -> dict[str]:
    """
    Returns a serialized list of all projects for a given election.

    Parameters
    ----------
        election_name: str,
            name of the election
        database: str = "default"
            name of the database to work on
    
    Returns
    -------
        dict
            "data":
                list of serialized Project objects
            "metadata":
                "rule_results_existing":
                    serialized list of rules that have been computed for this election,
                    this is needed to know whether a rule not present in the rules_selected_by field of the project
                    did not choose the project or was just not computed

    """
    if election_name == None:
        raise ApiExcepetion(
            "Please provide an election name with your request.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    project_query_set = Project.objects.using(database).all().filter(election__name=election_name)
    project_serializer = ProjectSerializer(project_query_set, many=True)

    rule_query_set = Rule.objects.using(database).all().filter(
        rule_results__election__name=election_name
    )
    rule_serializer = RuleSerializer(rule_query_set, many=True)

    return {
        "data": project_serializer.data,
        "metadata": {"rule_results_existing": rule_serializer.data},
    }


def get_rule_family_list(database: str = "default") -> dict[str, list[dict]]:
    """
    Returns a serialized nested list of all RuleFamily objects.

    Parameters
    ----------
        database: str = "default"
            name of the database to work on
    
    Returns
    -------
        dict
            "data":
                serialized nested list of all RuleFamily objects,
                the 'elements' field will be a serialized list of rules
                    
    """
    rule_family_query = RuleFamily.objects.using(database).all().filter(parent_family__isnull=True)
    rule_family_serializer = RuleFamilyFullSerializer(rule_family_query, many=True)
    return {"data": rule_family_serializer.data}


def get_rule_result_property_list(
    property_short_names: Iterable[str] = None,
    database: str = "default"
) -> dict[str, list[dict]]:
    """
    Returns a serialized list of RuleResultMetadata objects.

    Parameters
    ----------
        property_short_names: Iterable[str] = None
            list of short names of the properties requested, if None all properties will be returned
        database: str = "default"
            name of the database to work on
    
    Returns
    -------
        dict
            "data":
                serialized list of RuleResultMetadata objects
                    
    """
    query = RuleResultMetadata.objects.using(database).all()
    if property_short_names != None:
        query = query.filter(short_name__in=property_short_names)

    serializer = RuleResultMetadataSerializer(query, many=True)
    return {"data": serializer.data}


def get_filterable_election_property_list(
    property_short_names: Iterable[str] = None,
    ballot_type: str = None,
    database: str = "default"
) -> dict[str, list[dict[str, dict]]]:
    """
    Returns a serialized list of election properties, that are supported as filters.
    This is a combination of ElectionMetadata objects supporting the ballot type and all public Election model fields.
    The fields are 'translated' to look like serialized ElectionMetadata objects.
    Every property will thus be a dictionary with "name", "short_name", "description" and "inner_type".
    If "inner_type" is "reference" (e.g. if a field is ForeignKey), there will be another key "referencable_objects",
    containing all possible referenced objects of that election property, each with a "name" and "description" key.

    Parameters
    ----------
        property_short_names: Iterable[str]
            list of short names of the election properties requested, if None all properties will be returned
        ballot_type: str = None
            name of the ballot type, many properties not apply to some of them
        database: str = "default"
            name of the database to work on
    
    Returns
    -------
        dict
            "data":
                serialized list of ElectionMetadata objects
    """
    def field_to_property_dict(field_name):
        """
        Translates a django field to a dictionary with name, short_name, description, inner_type
        to match the structure of a serialized ElectionDataProperty.
        For ForeignKey fields also collects all possible referenced objects and saves them in the "referencable_objects" key
        """
        property_field = Election._meta.get_field(field_name)

        property_dict = {
            "name": property_field.verbose_name,
            "short_name": field_name,
            "description": property_field.help_text,
            "inner_type": _get_type_from_model_field(property_field),
        }

        if property_dict["inner_type"] == "reference":
            related_model_query_set = property_field.related_model.objects.using(database).all()
            related_model_query_set = related_model_query_set.annotate(
                num_elections=Count(property_field.remote_field.related_name)
            ).filter(num_elections__gt=0)
            referencable_objects = {}
            for obj in related_model_query_set:
                referencable_objects[obj.pk] = {
                    "name": obj.name,
                    "description": obj.description,
                }
            property_dict["referencable_objects"] = referencable_objects

        return property_dict

    properties = []

    for field_name in Election.public_fields:
        if property_short_names == None or field_name in property_short_names:
            properties.append(field_to_property_dict(field_name))

    property_query = ElectionMetadata.objects.using(database).all()
    if property_short_names != None:
        property_query = property_query.filter(short_name__in=property_short_names)
    if ballot_type != None:
        property_query = property_query.filter(applies_to=ballot_type)
    for metadata_obj in property_query:
        properties.append(ElectionMetadataSerializer(metadata_obj).data)

    return {
        "data": properties,
    }


def get_rule_result_average_data_properties(
    rule_abbr_list: Iterable[str],
    property_short_names: Iterable[str],
    election_filters: dict = {},
    include_incomplete_elections: bool = False,
    database: str = "default"
) -> dict[str]:
    """
    Returns for each given rule and rule result property, the average value of that property for the result of that rule.
    Only considers elections that have all given rules and rule result properties computed in the database.

    Parameters
    ----------
        rule_abbr_list: Iterable[str]
            list of abbreviations of the rules
        property_short_names: Iterable[str]
            list of short names of the election properties
        election_filters: dict = {}
            additional filters for the elections considered, see filter_elections method for details 
        database: str = "default"
            name of the database to work on
    
    Returns
    -------
        dict
            "data":
                dictionary containing the rule abbreviations as key and a dictionary as value,
                containing the property short names and their average value
            "metadata":
                "num_elections":
                    the number of election over which the average was taken
    """
    election_query_set = filter_elections(**election_filters, database=database)
    if not include_incomplete_elections:
        election_query_set = filter_elections_by_rule_properties(
            election_query_set,
            rule_abbr_list=rule_abbr_list,
            property_short_names=property_short_names,
            database=database
        )
    rule_result_data_property_query_set = RuleResultDataProperty.objects.using(database).all().filter(
        rule_result__election__in=election_query_set
    )

    data_dict = {}
    for rule in rule_abbr_list:
        data_dict[rule] = {}
        for prop_name in property_short_names:
            rule_result_metadata_obj = RuleResultMetadata.objects.using(database).get(
                short_name=prop_name
            )
            if (
                rule_result_metadata_obj.inner_type == "float"
                or rule_result_metadata_obj.inner_type == "int"
            ):
                data_dict[rule][prop_name] = (
                    rule_result_data_property_query_set.filter(
                        rule_result__rule__abbreviation=rule,
                        metadata__short_name=prop_name,
                    )
                    .annotate(value_as_float=Cast("value", FloatField()))
                    .aggregate(Avg("value_as_float"))["value_as_float__avg"]
                )

            elif rule_result_metadata_obj.inner_type == "list[float]":
                prop_list = []
                for (
                    rule_result_data_property
                ) in rule_result_data_property_query_set.filter(
                    rule_result__rule__abbreviation=rule, metadata__short_name=prop_name
                ).all():
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
    return {"data": data_dict, "meta_data": {"num_elections": len(election_query_set)}}


def get_satisfaction_histogram(
    rule_abbr_list: Iterable[str],
    election_filters: dict = {},
    include_incomplete_elections: bool = False,
    database: str = "default"
) -> dict[str, list[float]]:
    """
    Returns for each given rule, the satisfaction histogram for the result of that rule.
    This is more or less only a wrapper for calling get_rule_result_average_data_properties on the agg_nrmcost_sat property.

    Parameters
    ----------
        rule_abbr_list: Iterable[str]
            list of abbreviations of the rules
        election_filters: dict = {}
            additional filters for the elections considered, see filter_elections method for details 
        database: str = "default"
            name of the database to work on
    
    Returns
    -------
        dict
            "data":
                dictionary containing the rule abbreviations as key and a dictionary as value,
                containing "hist_data" (pabutools satisfaction_histogram result) and "avg" (average satisfaction)
            "metadata":
                "num_elections":
                    the number of election over which the average was taken
    """
    data_dict = get_rule_result_average_data_properties(
        rule_abbr_list,
        ["agg_nrmcost_sat", "avg_nrmcost_sat"],
        election_filters=election_filters,
        include_incomplete_elections=include_incomplete_elections,
        database=database
    )
    data_dict["data"] = {
        rule: {
            "hist_data": data_dict["data"][rule]["agg_nrmcost_sat"],
            "avg": data_dict["data"][rule]["avg_nrmcost_sat"],
        }
        for rule in data_dict["data"]
    }
    return data_dict


def get_election_property_histogram(
    election_property_short_name: str,
    election_filters: dict = {},
    num_bins: int = 20,
    by_ballot_type: bool = False,
    log_scale: bool = False,
    database: str = "default"
) -> tuple[list, list]:
    """
    Returns histogram data for a given election property

    Parameters
    ----------
        election_property_short_name: str
            short name of the election property
        election_filters: dict = {}
            additional filters for the elections considered, see filter_elections method for details 
        num_bins: int = 20
            number of histogram bins
        by_ballot_type: bool = False
            if True, th histogram data will be grouped by the ballot type,
            the bin selection will be made globally, but the values will be given for each ballot type separately
        log_scale: bool = False
            whether to use logarithmic scale for the histogram bins,
            if True, all values smaller or equal zero will be ignored
        database: str = "default"
            name of the database to work on
    
    Returns
    -------
        dict
            "data":
                dictionary containing the histogram data:
                    "bins":
                        list of length num_bins+1, containing all bin border values
                    "bin_midpoints":
                        list of middle points for each bin, useful for visualization
                    "values":
                        list of values for each bin if by_ballot_type is False
                        else dict with ballot type name as key and list of values for each bin as value
            "metadata":
                "election_property":
                    the serialized election property,
                    same format as get_filterable_election_property_list returns
    """
    ballot_type_names = [
        prop_tuple[0] for prop_tuple in BallotType.objects.using(database).all().values_list("name")
    ]

    election_query_set = filter_elections(**election_filters, database=database)

    election_meta_data_obj = ElectionMetadata.objects.using(database).filter(
        short_name=election_property_short_name
    )
    # if property is ElectionMetadata
    if election_meta_data_obj.exists():
        election_data_property_query = (
            ElectionDataProperty.objects.using(database).all()
            .filter(
                metadata__short_name=election_property_short_name,
                election__in=election_query_set,
            )
            .annotate(ballot_type=F("election__ballot_type__name"))
        )

        hist_data = histogram_data_from_query_set_and_field(
            query_set=election_data_property_query,
            field_name="value",
            by_category={
                "field_name": "election__ballot_type__name",
                "categories": ballot_type_names,
            }
            if by_ballot_type
            else None,
            num_bins=num_bins,
            log_scale=log_scale,
        )
    # if property is Election model field
    else:
        hist_data = histogram_data_from_query_set_and_field(
            query_set=election_query_set,
            field_name=election_property_short_name,
            by_category={
                "field_name": "ballot_type__name",
                "categories": ballot_type_names,
            }
            if by_ballot_type
            else None,
            num_bins=num_bins,
            log_scale=log_scale,
        )

    election_property = get_filterable_election_property_list(
        [election_property_short_name],
        database=database
    )["data"][0]

    return {"data": hist_data, "meta_data": {"election_property": election_property}}


def histogram_data_from_query_set_and_field(
    query_set: QuerySet,
    field_name: str,
    num_bins: int,
    by_category: dict = None,
    log_scale: bool = False
) -> dict[str, list]:
    """
    computes histogram data for a given query set and a model field of the corresponding model 

    Parameters
    ----------
        query_set: QuerySet
            the query set to compute on,
            make sure it is "using" the right database
        field_name: str
            name of the model field
        num_bins: int
            number of histogram bins
        by_category: dict = None
            if not None, will group the output into the given categories
            the dict should have the keys:
                "field_name":
                    the field name that holds the category for each object,
                    this can also be deeper in the model relations using the django double underscore (e.g. "object__related__field_name") 
                "categories":
                    all possible categories of that field
        log_scale: bool = False
            whether to use logarithmic scale for the histogram bins,
            if True, all values smaller or equal zero will be ignored
    
    Returns
    -------
        dictionary
            "bins":
                list of length num_bins+1, containing all bin border values
            "bin_midpoints":
                list of middle points for each bin, useful for visualization
            "values":
                list of values for each bin if by_category is None
                else dict with category name as key and list of values for each bin as value
    """
    # making sure all values are positive if log scale is chosen
    if log_scale:
        query_set = query_set.filter(**{field_name + "__gt": 0})

    if by_category:
        query_sets_by_category = {
            category: query_set.filter(**{by_category["field_name"]: category})
            for category in by_category["categories"]
        }
        
    # special case: no elements in query set
    if (not query_set.exists()):
        return {
            "bins": [],
            "bin_midpoints": [],
            "values": [],
        }

    min_value = float(query_set.aggregate(Min(field_name))[field_name + "__min"])
    max_value = float(query_set.aggregate(Max(field_name))[field_name + "__max"])

    # special case: all elements have the same value
    if min_value == max_value:
        if by_category:
            values = {
                category: [query_sets_by_category[category].count()]
                for category in by_category["categories"]
            }
        else:
            values = [query_set.count()]
        return {
            "bins": [min_value, min_value],
            "bin_midpoints": [min_value],
            "values": values,
        }

    # computing the annotation formula for annotating each element in the query set with an integer corresponding to the bin
    if log_scale:
        bins = [
            min_value * (max_value / min_value) ** (float(i) / num_bins)
            for i in range(num_bins + 1)
        ]
        bin_midpoints = [
            min_value * (max_value / min_value) ** (float(i + 0.5) / num_bins)
            for i in range(num_bins)
        ]
        annotation_formula = Floor(
            Ln(Cast(field_name, FloatField()) / min_value)
            / Ln(max_value / min_value)
            * num_bins
        )
    else:
        bins = [
            min_value + i * (max_value - min_value) / num_bins
            for i in range(num_bins + 1)
        ]
        bin_midpoints = [
            min_value + (i + 0.5) * (max_value - min_value) / num_bins
            for i in range(num_bins)
        ]
        annotation_formula = Floor(
            (Cast(field_name, FloatField()) - min_value)
            / (max_value - min_value)
            * num_bins
        )

    # defining the counting formulas for counting the number of objects annotated with each bin id
    counters = {str(i): Count("id", filter=Q(hist_bin=i)) for i in range(num_bins - 1)}
    counters[str(num_bins - 1)] = Count(
        "id", filter=Q(hist_bin__in=[num_bins - 1, num_bins])
    )  # last bin should be closed interval

    # finally annotating the objects using the annotation formula and counting them using the counting formulas
    if by_category:
        for category in by_category["categories"]:
            query_sets_by_category[category] = query_sets_by_category[
                category
            ].annotate(hist_bin=annotation_formula)

        histogram_data_values = {
            category: list(
                query_sets_by_category[category].aggregate(**counters).values()
            )
            for category in by_category["categories"]
        }
    else:
        query_set = query_set.annotate(hist_bin=annotation_formula)
        histogram_data_values = list(query_set.aggregate(**counters).values())

    histogram_data = {
        "bins": bins,
        "bin_midpoints": bin_midpoints,
        "values": histogram_data_values,
    }
    return histogram_data


# could be optimized (looping through categories probably not necessary)
def category_proportions(
    election_name: str,
    rule_abbreviation_list: str,
    database: str = "default"
) -> dict:
    """
    Returns category proportions for a given election and a list of rule

    Parameters
    ----------
        election_name: str,
            name of the election
        rule_abbreviation_list: str
            abbreviations of the rules
        database: str = "default"
            name of the database to work on
    
    Returns
    -------
        dict
            "data": dict
                "category_names":
                    list of category names of the election
                "vote_cost_shares":
                    list of vote cost shares for the categories,
                    that is the total number of votes of each project in the category times its cost, normalized
                "result_cost_shares":
                    dictionary, for each rule short name the list of result cost shares for the categories,
                    that is the sum of costs of selected projects in the category, normalized
    """
    try:
        election_obj = Election.objects.using(database).all().get(name=election_name)
    except:
        raise ApiExcepetion(
            "Invalid election name.", status_code=status.HTTP_400_BAD_REQUEST
        )

    if election_obj.has_categories:
        categories_query = Category.objects.using(database).all().filter(election=election_obj)
        votes = PreferenceInfo.objects.using(database).all().filter(voter__election=election_obj)

        category_names = []
        vote_cost_shares = []
        vote_cost_share_sum = 0
        result_cost_shares = {
            rule_abbreviation: [] for rule_abbreviation in rule_abbreviation_list
        }
        result_cost_share_sums = {
            rule_abbreviation: 0 for rule_abbreviation in rule_abbreviation_list
        }
        for category_obj in categories_query:
            category_names.append(category_obj.name)

            vote_cost_share_formula = Sum(
                F("project__cost") * F("preference_strength"),
                output_field=FloatField(),
                default=0,
            )
            vote_cost_share = votes.filter(project__categories=category_obj).aggregate(
                vote_cost_share=vote_cost_share_formula
            )
            vote_cost_shares.append(vote_cost_share["vote_cost_share"])
            vote_cost_share_sum += vote_cost_share["vote_cost_share"]

            for rule_abbreviation in rule_abbreviation_list:
                projects_selected = Project.objects.using(database).all().filter(
                    election=election_obj,
                    rule_results_selected_by__rule__abbreviation=rule_abbreviation,
                )
                result_cost_share_formula = Sum(
                    "cost", output_field=FloatField(), default=0
                )
                result_cost_share = projects_selected.filter(
                    categories=category_obj
                ).aggregate(result_cost_share=result_cost_share_formula)
                result_cost_shares[rule_abbreviation].append(
                    result_cost_share["result_cost_share"]
                )
                result_cost_share_sums[rule_abbreviation] += result_cost_share[
                    "result_cost_share"
                ]

        if vote_cost_share_sum == 0:
            raise ApiExcepetion(
                "Election does not have votes for projects with positive cost and categories.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # if a rule does not select any projects with positive cost and categories:
        # set the divider to 1 to avoid dividing by 0, all values will be zero for that rule
        for rule_abbreviation in rule_abbreviation_list:
            if result_cost_share_sums[rule_abbreviation] == 0:
                result_cost_share_sums[rule_abbreviation] = 1

        for i in range(len(category_names)):
            vote_cost_shares[i] /= vote_cost_share_sum
            for rule_abbreviation in rule_abbreviation_list:
                result_cost_shares[rule_abbreviation][i] /= result_cost_share_sums[
                    rule_abbreviation
                ]
    else:
        category_names, vote_cost_shares = [], []
        result_cost_shares = {
            rule_abbreviation: [] for rule_abbreviation in rule_abbreviation_list
        }
    return {
        "data": {
            "category_names": category_names,
            "vote_cost_shares": vote_cost_shares,
            "result_cost_shares": result_cost_shares,
        }
    }


def filter_elections(
    election_query_set: QuerySet | None = None,
    database: str = "default",
    **election_filters
) -> QuerySet:
    # """
    # Returns histogram data for a given election property

    # Parameters
    # ----------
    #     election_property_short_name: str
    #         short name of the elecion property
    #     election_filters: dict = {}
    #         additional filters for the elections considered, see filter_elections method for details 
    #     num_bins: int = 20
    #         number of histogram bins
    #     by_ballot_type: bool = False
    #         if True, th histogramm data will be grouped by the ballot type,
    #         the bin selection will be made globally, but the values will be given for each ballot type separately
    #     log_scale: bool = False
    #         whether to use logarithmic scale for the histogram bins,
    #         if True, all values smaller or equal zero will be ignored
    #     database: str = "default"
    #         name of the database to work on
    
    # Returns
    # -------
    #     dict
    #         "data":
    #             dictionary containing the histogram data:
    #                 "bins":
    #                     list of length num_bins+1, containing all bin border values
    #                 "bin_midpoints":
    #                     list of middle points for each bin, useful for visualization
    #                 "values":
    #                     list of values for each bin if by_ballot_type is False
    #                     else dict with ballot type name as key and list of values for each bin as value
    #         "metadata":
    #             "election_property":
    #                 the serialized election property,
    #                 same format as get_filterable_election_property_list returns
    # """
    if election_query_set == None:
        election_query_set = Election.objects.using(database).all()

    for election_property in election_filters:
        if election_property in Election.public_fields:
            election_query_set = _filter_elections_by_model_field(
                election_query_set=election_query_set,
                election_property=election_property,
                election_property_filter=election_filters[election_property],
            )
        elif (
            ElectionMetadata.objects.using(database).all().filter(short_name=election_property).exists()
        ):
            election_query_set = _filter_elections_by_metadata(
                election_query_set=election_query_set,
                election_property=election_property,
                election_property_filter=election_filters[election_property],
            )
        else:
            # property does not exist or is not allowed to be filtered through the api
            raise ApiExcepetion(
                "Property {} does not exist or is not supported for filtering.".format(
                    election_property
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    return election_query_set


def _filter_elections_by_model_field(
    election_query_set: QuerySet,
    election_property: str,
    election_property_filter
) -> QuerySet:
    type = _get_type_from_model_field(Election._meta.get_field(election_property))
    if type == "int" or type == "float":
        if (
            "min" in election_property_filter
            and election_property_filter["min"] != None
        ):
            election_query_set = election_query_set.filter(
                **{election_property + "__gte": election_property_filter["min"]}
            )
        if (
            "max" in election_property_filter
            and election_property_filter["max"] != None
        ):
            election_query_set = election_query_set.filter(
                **{election_property + "__lte": election_property_filter["max"]}
            )
    elif type == "date":
        if (
            "min" in election_property_filter
            and election_property_filter["min"] != None
        ):
            election_query_set = election_query_set.filter(
                **{
                    election_property
                    + "__gte": datetime.date(election_property_filter["min"])
                }
            )
        if (
            "max" in election_property_filter
            and election_property_filter["max"] != None
        ):
            election_query_set = election_query_set.filter(
                **{
                    election_property
                    + "__lte": datetime.date(election_property_filter["max"])
                }
            )
    elif type == "bool":
        if election_property_filter != None:
            election_query_set = election_query_set.filter(
                **{election_property: election_property_filter}
            )
    elif type == "str":
        if (
            "contains" in election_property_filter
            and election_property_filter["contains"] != None
        ):
            election_query_set = election_query_set.filter(
                **{
                    election_property
                    + "__icontains": election_property_filter["contains"]
                }
            )
        if (
            "equals" in election_property_filter
            and election_property_filter["equals"] != None
        ):
            election_query_set = election_query_set.filter(
                **{election_property: election_property_filter["equals"]}
            )
    elif type == "reference":
        if isinstance(election_property_filter, str):
            election_query_set = election_query_set.filter(
                **{election_property: election_property_filter}
            )
        elif isinstance(election_property_filter, list) and all(
            isinstance(item, str) for item in election_property_filter
        ):
            election_query_set = election_query_set.filter(
                **{election_property + "__in": election_property_filter}
            )
        else:
            raise ApiExcepetion(
                "Wrong type of filter {}. Should be either a string or a list of strings.".format(
                    type
                )
            )
    else:
        # other types (e.g. foreign keys) not yet supported, if you add a field of a different type, write a filter here
        raise NotImplementedError(
            "Property type {} is not supported for filtering.".format(type)
        )

    return election_query_set


def _filter_elections_by_metadata(
    election_query_set: QuerySet,
    election_property: str,
    election_property_filter
) -> QuerySet:
    # no type check, because all election meta properties are numbers
    if "min" in election_property_filter and election_property_filter["min"] != None:
        election_query_set = election_query_set.filter(
            data_properties__metadata__short_name=election_property,
            data_properties__value__gte=election_property_filter["min"],
        )
    if "max" in election_property_filter and election_property_filter["max"] != None:
        election_query_set = election_query_set.filter(
            data_properties__metadata__short_name=election_property,
            data_properties__value__lte=election_property_filter["max"],
        )

    return election_query_set


def filter_elections_by_rule_properties(
    election_query_set: QuerySet,
    rule_abbr_list: Iterable[str] = [],
    property_short_names: Iterable[str] = [],
    database: str = "default"
) -> QuerySet:
    for rule in rule_abbr_list:
        rule_result_query_set = RuleResult.objects.using(database).all().filter(rule__abbreviation=rule)
        for prop in property_short_names:
            rule_result_query_set = rule_result_query_set.filter(
                Q(data_properties__metadata__short_name=prop)
            )

        election_query_set = election_query_set.filter(
            Q(rule_results__in=rule_result_query_set)
        )

    return election_query_set


def handle_file_upload(pb_file):
    """
    WORK IN PROGRESS
    """
    rule_lists = {
        "approval": ["greedy_cost", "max_cost", "mes_cost", "seq_phragmen"],
        "ordinal": ["greedy_borda", "max_borda", "mes_borda"],
        "cumulative": ["greedy_cardbal", "max_add_card", "mes_cardbal"],
        "cardinal": ["greedy_cardbal", "max_add_card", "mes_cardbal"],
    }
    
    fs = FileSystemStorage()
    file_path = "tmp/" + pb_file.name + f"_{random.randint(0, 10000):}"
    fs.save(file_path, pb_file)
    
    remove_old_user_elections()
    
    try:
        election_obj = add_election(
            file_path=file_path,
            override=True,
            database="user_submitted",
            size_limits={
                "votes": 5000,
                "projects": 20
            },
            verbosity=3
        )
        compute_election_properties(
            [election_obj.name],
            exact=False,
            override=True,
            use_db=True,
            database="user_submitted",
            verbosity=3
        )
        compute_rule_results(
            [election_obj.name],
            rule_list=rule_lists[election_obj.ballot_type.name],
            exact=False,
            override=True,
            use_db=True,
            database="user_submitted",
            verbosity=3,
        )
        compute_rule_result_properties(
            [election_obj.name],
            exact=False,
            override=True,
            use_db=True,
            database="user_submitted",
            verbosity=3,
        )
    except Exception as e:
        raise ApiExcepetion(str(e), status_code=status.HTTP_406_NOT_ACCEPTABLE)
    finally:
        fs.delete(file_path)

    return {"election_name": election_obj.name}