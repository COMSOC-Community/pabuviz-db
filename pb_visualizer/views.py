import os
import json
from django.conf import settings
from django.http import HttpResponse
from time import sleep
from rest_framework.response import Response
from rest_framework.decorators import api_view

from pb_visualizer.serializers import *
from pb_visualizer.api import *

caching_parameters = {"cache-control": "max-age=1"}

@api_view(["GET"])
def api_documentation(request):
    if request.method == "GET":
        file_path = os.path.join(settings.BASE_DIR, 'pb_visualizer/docs/docs.html')
        with open(file_path, 'r') as file:
            html_content = file.read()
        return HttpResponse(html_content, content_type='text/html')

@api_view(["GET"])
def election_list(request):
    if request.method == "GET":
        filters = json.loads(request.GET.get("filters", "{}"))
        data = get_election_list(filters)
        return Response(data, headers=caching_parameters)


@api_view(["GET"])
def election_details(request):
    if request.method == "GET":
        filters = json.loads(request.GET.get("filters", "{}"))
        property_short_names = json.loads(
            request.GET.get("property_short_names", "null")
        )
        ballot_type = json.loads(request.GET.get("ballot_type", "null"))
        user_submitted = json.loads(request.GET.get("user_submitted", "null"))
        database =  "user_submitted" if user_submitted else "default"  

        data = get_election_details(
            property_short_names=property_short_names,
            ballot_type=ballot_type,
            filters=filters,
            database=database
        )
        return Response(data, headers=caching_parameters)


@api_view(["GET"])
def election_property_values_list(request):
    if request.method == "GET":
        property_short_name = json.loads(request.GET.get("property_short_name", "null"))
        ballot_type = json.loads(request.GET.get("ballot_type", "null"))
        user_submitted = json.loads(request.GET.get("user_submitted", "null"))
        database =  "user_submitted" if user_submitted else "default"  

        data = get_election_property_values_list(
            property_short_name=property_short_name,
            ballot_type=ballot_type,
            database=database
        )
        return Response(data, headers=caching_parameters)


@api_view(["GET"])
def project_list(request):
    if request.method == "GET":
        election_name = json.loads(request.GET.get("election_name", "null"))
        user_submitted = json.loads(request.GET.get("user_submitted", "null"))
        database =  "user_submitted" if user_submitted else "default"  
        data = get_project_list(election_name, database=database)
        return Response(data, headers=caching_parameters)


@api_view(["GET"])
def rule_family_list(request):
    if request.method == "GET":
        data = get_rule_family_list()
        return Response(data, headers=caching_parameters)


@api_view(["GET"])
def ballot_type_list(request):
    if request.method == "GET":
        data = get_ballot_type_list()
        return Response(data, headers=caching_parameters)


@api_view(["GET"])
def rule_result_property_list(request):
    if request.method == "GET":
        property_short_names = json.loads(request.GET.get("property_short_names", "null"))
        data = get_rule_result_property_list(property_short_names)
        return Response(data, headers=caching_parameters)


@api_view(["GET"])
def filterable_election_property_list(request):
    if request.method == "GET":
        property_short_names = json.loads(request.GET.get("property_short_names", "null"))
        ballot_type = json.loads(request.GET.get("ballot_type", "null"))
        data = get_filterable_election_property_list(
            property_short_names, ballot_type=ballot_type
        )
        return Response(data, headers=caching_parameters)


@api_view(["GET"])
def rule_result_data_property(request):
    if request.method == "GET":
        rule_abbr_list = json.loads(request.GET.get("rule_abbr_list", "[]"))
        property_short_names = json.loads(request.GET.get("property_short_names", "[]"))
        election_filters = json.loads(request.GET.get("election_filters", "{}"))
        include_incomplete_elections = json.loads(request.GET.get("include_incomplete_elections", "false"))
        user_submitted = json.loads(request.GET.get("user_submitted", "null"))
        database =  "user_submitted" if user_submitted else "default"  
        data_dict = get_rule_result_average_data_properties(
            rule_abbr_list=rule_abbr_list,
            property_short_names=property_short_names,
            election_filters=election_filters,
            include_incomplete_elections=include_incomplete_elections,
            database=database
        )

        return Response(data_dict, headers=caching_parameters)


@api_view(["GET"])
def voter_satisfaction_histogram(request):
    if request.method == "GET":
        rule_abbr_list = json.loads(request.GET.get("rule_abbr_list", "[]"))
        election_filters = json.loads(request.GET.get("election_filters", "{}"))
        include_incomplete_elections = json.loads(request.GET.get("include_incomplete_elections", "false"))
        user_submitted = json.loads(request.GET.get("user_submitted", "null"))
        database =  "user_submitted" if user_submitted else "default"  
        data_dict = get_satisfaction_histogram(
            rule_abbr_list=rule_abbr_list,
            election_filters=election_filters,
            include_incomplete_elections=include_incomplete_elections,
            database=database
        )
        return Response(data_dict, headers=caching_parameters)


@api_view(["GET"])
def election_property_histogram(request):
    if request.method == "GET":
        election_property_short_name = json.loads(
            request.GET.get("election_property_short_name", "null")
        )
        election_filters = json.loads(request.GET.get("election_filters", "{}"))
        num_bins = json.loads(request.GET.get("num_bins", "20"))
        by_ballot_type = json.loads(request.GET.get("by_ballot_type", "false"))
        log_scale = json.loads(request.GET.get("log_scale", "false"))

        hist_data = get_election_property_histogram(
            election_property_short_name=election_property_short_name,
            election_filters=election_filters,
            num_bins=num_bins,
            by_ballot_type=by_ballot_type,
            log_scale=log_scale,
        )
        return Response(hist_data, headers=caching_parameters)


@api_view(["GET"])
def rule_category_proportions(request):
    if request.method == "GET":
        election_name = json.loads(request.GET.get("election_name", "null"))
        rule_abbreviation_list = json.loads(
            request.GET.get("rule_abbreviation_list", "{}")
        )
        user_submitted = json.loads(request.GET.get("user_submitted", "null"))
        database =  "user_submitted" if user_submitted else "default"  
        category_proportion_data = category_proportions(
            election_name=election_name,
            rule_abbreviation_list=rule_abbreviation_list,
            database=database
        )
        return Response(category_proportion_data, headers=caching_parameters)



@api_view(["POST"])
def submit_pb_file(request):
    if request.method == "POST":
        pb_file = request.FILES.get("pb_file")
        response_data = handle_file_upload(pb_file)
        return Response(response_data, headers=caching_parameters)
