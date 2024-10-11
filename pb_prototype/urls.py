"""
URL configuration for pb_prototype project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from pb_visualizer import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", views.api_documentation),
    path("api/ballot_types/", views.ballot_type_list),
    path("api/elections/", views.election_list),
    path("api/election_details/", views.election_details),
    path("api/election_properties/", views.filterable_election_property_list),
    path("api/election_property_values_list/", views.election_property_values_list),
    path("api/projects/", views.project_list),
    path("api/rules/", views.rule_family_list),
    path("api/rule_properties/", views.rule_result_property_list),
    path("api/avg_rule_property/", views.rule_result_data_property),
    path("api/rule_voter_satisfaction_histogram/", views.voter_satisfaction_histogram),
    path("api/election_property_histogram/", views.election_property_histogram),
    path("api/category_proportions/", views.rule_category_proportions),
    path("api/submit_pb_file/", views.submit_pb_file),
]
