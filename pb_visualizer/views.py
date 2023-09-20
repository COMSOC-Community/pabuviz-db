import json
from time import sleep
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from pb_visualizer.models import Rule
from pb_visualizer.serializers import *
from pb_visualizer.api import *

from collections import defaultdict
from django.core import serializers
from django.db.models import Q, Avg


@api_view(["POST"])
def election_list(request):
    if request.method == "POST":
        body = json.loads(request.body)

        filters = {}
        if "filters" in body:
            filters = body["filters"]

        try:
            data = get_election_list(filters)
            return Response(data)
        except Exception as e:
            return Response(status=404, exception=e)


@api_view(["POST"])
def election_details(request):
    if request.method == "POST":
        body = json.loads(request.body)

        filters = {}
        if "filters" in body:
            filters = body["filters"]
        property_short_names = None
        if "property_short_names" in body:
            property_short_names = body["property_short_names"]
        ballot_type = None
        if "ballot_type" in body:
            ballot_type = body["ballot_type"]

        data = get_election_details(
            property_short_names=property_short_names,
            ballot_type=ballot_type,
            filters=filters,
        )
        return Response(data)
        # try:
        # except Exception as e:
        #     return Response(status=404, exception=e)


# @api_view(['POST'])
# def election_metadata(request, election_id):
#     if request.method == 'POST':
#         election_obj = Election.objects.get(id=election_id)
#         election_serializer = ElectionSerializerFull(election_obj)

#         meta_dict = election_serializer.data
#         data_property_objs = ElectionDataProperty.objects.filter(election=election_obj).all()
#         for data_property_obj in data_property_objs:
#             meta_dict[data_property_obj.metadata.short_name] = data_property_obj.value
#             meta_dict['labels'][data_property_obj.metadata.short_name] = {
#                 'label': data_property_obj.metadata.name,
#                 'help_text': data_property_obj.metadata.description
#             }
#         return Response(meta_dict)


@api_view(["POST"])
def project_list(request):
    if request.method == "POST":
        body = json.loads(request.body)

        # try:
        data = get_project_list(body["election_id"])
        return Response(data)
        # except Exception as e:
        #     return Response(status=404, exception=e)


@api_view(["POST"])
def rule_family_list(request):
    if request.method == "POST":
        data = get_rule_family_list()
        return Response(data)


@api_view(["POST"])
def ballot_type_list(request):
    if request.method == "POST":
        data = get_ballot_type_list()
        return Response(data)


# @api_view(['POST'])
# def rule_result(request, election_id, rule_abbreviation):
#     if request.method == 'POST':
#         try:
#             rule_result_obj = RuleResult.objects.get(election=election_id,
#                                                      rule__abbreviation=rule_abbreviation)
#         except RuleResult.DoesNotExist:
#             return Response(status=404)

#         rule_result_serializer = RuleResultSerializer(rule_result_obj)
#         meta_dict = rule_result_serializer.data
#         data_property_objs = RuleResultDataProperty.objects.filter(rule_result=rule_result_obj).all()
#         for data_property_obj in data_property_objs:
#             meta_dict[data_property_obj.metadata.short_name] = data_property_obj.value
#             meta_dict['labels'][data_property_obj.metadata.short_name] = {
#                 'label': data_property_obj.metadata.name,
#                 'help_text': data_property_obj.metadata.description
#             }

#         return Response(meta_dict)


@api_view(["POST"])
def rule_result_property_list(request):
    if request.method == "POST":
        body = json.loads(request.body)

        property_short_names = []
        if "property_short_names" in body:
            property_short_names = body["property_short_names"]

        try:
            data = get_rule_result_property_list(property_short_names)
            return Response(data)
        except Exception as e:
            return Response(status=404, exception=e)


@api_view(["POST"])
def filterable_election_property_list(request):
    if request.method == "POST":
        body = json.loads(request.body)
        property_short_names = []
        if "property_short_names" in body:
            property_short_names = body["property_short_names"]
        ballot_type = None
        if "ballot_type" in body:
            ballot_type = body["ballot_type"]

        try:
            data = get_filterable_election_property_list(
                property_short_names, ballot_type=ballot_type
            )
            return Response(data)
        except Exception as e:
            return Response(status=404, exception=e)


@api_view(["POST"])
def rule_result_data_property(request):
    if request.method == "POST":
        body = json.loads(request.body)

        data_dict = get_rule_result_average_data_properties(
            rule_abbr_list=body["rule_abbr_list"],
            property_short_names=body["property_short_names"],
            election_filters=body["election_filters"],
        )

        return Response(data_dict)

        # return Response(status=404, exception=e)


@api_view(["POST"])
def voter_satisfaction_histogram(request):
    if request.method == "POST":
        body = json.loads(request.body)

        data_dict = get_satisfaction_histogram(
            rule_abbr_list=body["rule_abbr_list"],
            election_filters=body["election_filters"],
        )
        return Response(data_dict)


@api_view(["POST"])
def election_property_histogram(request):
    if request.method == "POST":
        body = json.loads(request.body)

        hist_data = get_election_property_histogram(
            election_property_short_name=body["election_property_short_name"],
            election_filters=body["election_filters"],
            by_ballot_type=body["by_ballot_type"],
            num_bins=body["num_bins"],
            log_scale=body["log_scale"],
        )
        return Response(hist_data)


@api_view(["POST"])
def rule_category_proportions(request):
    if request.method == "POST":
        body = json.loads(request.body)

        try:
            category_proportion_data = category_proportions(
                body["election_id"], body["rule_abbreviation_list"]
            )
            return Response(category_proportion_data)
        except Exception as e:
            return Response(status=404, exception=e)
