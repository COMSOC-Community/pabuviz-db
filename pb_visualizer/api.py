from collections.abc import Iterable
import datetime
import json
from time import sleep


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

from rest_framework.exceptions import PermissionDenied
from rest_framework import status


class ApiExcepetion(PermissionDenied):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bad request"
    default_code = "invalid"

    def __init__(self, detail, status_code=None):
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code


def _get_type_from_model_field(field):
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


def get_ballot_type_list() -> list[dict]:
    ballot_type_query = BallotType.objects.all()
    ballot_type_query = ballot_type_query.annotate(
        num_elections=Count("elections")
    ).order_by("order_priority")
    ballot_type_query = ballot_type_query.filter(num_elections__gt=0)
    ballot_type_serializer = BallotTypeSerializer(ballot_type_query, many=True)

    return {"data": ballot_type_serializer.data}


def get_election_list(filters: dict) -> list[dict]:
    election_query_set = filter_elections(**filters)
    election_serializer = ElectionSerializer(election_query_set, many=True)

    ballot_type_query = (
        BallotType.objects.all().filter(elections__in=election_query_set).distinct()
    )
    ballot_type_serializer = BallotTypeSerializer(ballot_type_query, many=True)

    return {
        "data": election_serializer.data,
        "metadata": {"ballot_types": ballot_type_serializer.data},
    }


def get_election_details(
    property_short_names, ballot_type: str, filters: dict
) -> list[dict]:
    election_query_set = filter_elections(**filters)
    election_details_collection = {}

    properties = get_filterable_election_property_list(
        property_short_names=property_short_names, ballot_type=ballot_type
    )["data"]

    for election_obj in election_query_set:
        election_dict = ElectionSerializer(election_obj).data

        election_details = {}

        # first we get all the properties that are fields of the election model
        for property in properties:
            if property["short_name"] in Election.public_fields:
                election_details[property["short_name"]] = election_dict[
                    property["short_name"]
                ]

        # then we get all the properties that are ElectionMetadata
        data_props_query = ElectionDataProperty.objects.all().filter(
            election=election_obj,
            metadata__short_name__in=[p["short_name"] for p in properties],
        )
        for data_prop_obj in data_props_query:
            election_details[data_prop_obj.metadata.short_name] = data_prop_obj.value

        election_details_collection[election_obj.name] = election_details

    return {"data": election_details_collection, "metadata": properties}


def get_project_list(election_name: int) -> list[dict]:
    if election_name == None:
        raise ApiExcepetion(
            "Please provide an election name with your request.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    project_query_set = Project.objects.all().filter(election__name=election_name)
    project_serializer = ProjectSerializer(project_query_set, many=True)

    rule_query_set = Rule.objects.all().filter(
        rule_results__election__name=election_name
    )
    rule_serializer = RuleSerializer(rule_query_set, many=True)

    return {
        "data": project_serializer.data,
        "metadata": {"rule_results_existing": rule_serializer.data},
    }


def get_rule_family_list() -> list[dict]:
    rule_family_query = RuleFamily.objects.all().filter()
    rule_family_serializer = RuleFamilyFullSerializer(rule_family_query, many=True)

    return {"data": rule_family_serializer.data}


def get_rule_result_property_list(
    property_short_names: Iterable[str] = None,
) -> list[dict]:
    query = RuleResultMetadata.objects.all()
    if property_short_names != None:
        query = query.filter(short_name__in=property_short_names)

    serializer = RuleResultMetadataSerializer(query, many=True)
    return {"data": serializer.data}


def get_filterable_election_property_list(
    property_short_names: Iterable[str], ballot_type: str = None
) -> list[dict]:
    def field_to_property_dict(field_name):
        property_field = Election._meta.get_field(field_name)

        property_dict = {
            "name": property_field.verbose_name,
            "short_name": field_name,
            "description": property_field.help_text,
            "inner_type": _get_type_from_model_field(property_field),
        }

        if property_dict["inner_type"] == "reference":
            related_model_query_set = property_field.related_model.objects.all()
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
    referencable_objects = {}

    for field_name in Election.public_fields:
        if property_short_names == None or field_name in property_short_names:
            properties.append(field_to_property_dict(field_name))

    property_query = ElectionMetadata.objects.all()
    if property_short_names != None:
        property_query = property_query.filter(short_name__in=property_short_names)
    if ballot_type != None:
        property_query = property_query.filter(applies_to=ballot_type)
    for metadata_obj in property_query:
        properties.append(ElectionMetadataSerializer(metadata_obj).data)

    return {
        "data": properties,
        "metadata": {"referencable_objects": referencable_objects},
    }


def get_rule_result_average_data_properties(
    rule_abbr_list: Iterable[str],
    property_short_names: Iterable[str],
    election_filters: dict = {},
) -> dict[str, dict[str, float]]:
    election_query_set = filter_elections(**election_filters)
    election_query_set = filter_elections_by_rule_properties(
        election_query_set,
        rule_abbr_list=rule_abbr_list,
        property_short_names=property_short_names,
    )
    rule_result_data_property_query_set = RuleResultDataProperty.objects.all().filter(
        rule_result__election__in=election_query_set
    )

    data_dict = {}
    for rule in rule_abbr_list:
        data_dict[rule] = {}
        for prop_name in property_short_names:
            rule_result_metadata_obj = RuleResultMetadata.objects.get(
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
    rule_abbr_list: Iterable[str], election_filters: dict = {}
) -> dict[str, list[float]]:
    data_dict = get_rule_result_average_data_properties(
        rule_abbr_list,
        ["agg_nrmcost_sat", "avg_nrmcost_sat"],
        election_filters=election_filters,
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
) -> tuple[list, list]:
    ballot_type_names = [
        prop_tuple[0] for prop_tuple in BallotType.objects.all().values_list("name")
    ]

    election_query_set = filter_elections(**election_filters)

    election_meta_data_obj = ElectionMetadata.objects.filter(
        short_name=election_property_short_name
    )
    if election_meta_data_obj.exists():
        election_data_property_query = (
            ElectionDataProperty.objects.all()
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
        [election_property_short_name]
    )["data"][0]

    return {"data": hist_data, "meta_data": {"election_property": election_property}}


def histogram_data_from_query_set_and_field(
    query_set: QuerySet,
    field_name: str,
    num_bins: int,
    by_category: dict = None,
    log_scale: bool = False,
) -> tuple[list, list]:
    # making sure all values are positive if log scale is chosen
    if log_scale:
        query_set = query_set.filter(**{field_name + "__gt": 0})

    if by_category:
        query_sets_by_category = {
            category: query_set.filter(**{by_category["field_name"]: category})
            for category in by_category["categories"]
        }
        
    if (not query_set.exists()):
        return {
            "bins": [],
            "bin_midpoints": [],
            "values": [],
        }

    min_value = float(query_set.aggregate(Min(field_name))[field_name + "__min"])
    max_value = float(query_set.aggregate(Max(field_name))[field_name + "__max"])

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

    counters = {str(i): Count("id", filter=Q(hist_bin=i)) for i in range(num_bins - 1)}
    counters[str(num_bins - 1)] = Count(
        "id", filter=Q(hist_bin__in=[num_bins - 1, num_bins])
    )  # last bin should be closed interval

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
def category_proportions(election_name: int, rule_abbreviation_list: str):
    try:
        election_obj = Election.objects.all().get(name=election_name)
    except:
        raise ApiExcepetion(
            "Invalid election name.", status_code=status.HTTP_400_BAD_REQUEST
        )

    if election_obj.has_categories:
        categories_query = Category.objects.all().filter(election=election_obj)
        votes = PreferenceInfo.objects.all().filter(voter__election=election_obj)

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
                projects_selected = Project.objects.all().filter(
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
        "category_names": category_names,
        "vote_cost_shares": vote_cost_shares,
        "result_cost_shares": result_cost_shares,
    }


def filter_elections(
    election_query_set: QuerySet | None = None, **election_filters
) -> QuerySet:
    if election_query_set == None:
        election_query_set = Election.objects.all()

    for election_property in election_filters:
        if election_property in Election.public_fields:
            election_query_set = _filter_elections_by_model_field(
                election_query_set=election_query_set,
                election_property=election_property,
                election_property_filter=election_filters[election_property],
            )
        elif (
            ElectionMetadata.objects.all().filter(short_name=election_property).exists()
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
    election_query_set: QuerySet, election_property: str, election_property_filter
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
    election_query_set: QuerySet, election_property: str, election_property_filter
) -> QuerySet:
    # no type check, because all meta properties are numbers
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
