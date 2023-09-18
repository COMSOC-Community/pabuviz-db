from collections.abc import Iterable
from pb_visualizer.models import *
from pabutools import election as pbelection
import pabutools.fractions as fractions
import numpy as np



def project_object_to_pabutools(project: Project):
    return pbelection.Project(project.project_id,
                              fractions.str_as_frac(str(project.cost)),
                              [category.name for category in project.categories.all()],
                              [target.name for target in project.targets.all()])


def election_object_to_pabutools(election: Election) -> tuple[pbelection.Instance, pbelection.Profile]:
    categories = {cat.name for cat in election.categories.all()}
    targets = {tar.name for tar in election.targets.all()}
    projects = {project.project_id: project_object_to_pabutools(project) for project in election.projects.all()}

    instance = pbelection.Instance(budget_limit=fractions.str_as_frac(str(election.budget)), categories=categories, targets=targets)
    instance.update(projects.values())
    
    profile = None
    if election.ballot_type.name == 'approval':
        profile = pbelection.ApprovalMultiProfile(legal_min_length=election.get_meta_property("min_length"),
                                                  legal_max_length=election.get_meta_property("max_length"),
                                                  legal_min_cost=election.get_meta_property("min_cost"),
                                                  legal_max_cost=election.get_meta_property("max_cost"))
        for voter in election.voters.all():
            profile.append(pbelection.FrozenApprovalBallot([projects[project.project_id] for project in voter.votes.all()]))
    elif election.ballot_type.name == 'ordinal':
        profile = pbelection.OrdinalProfile(legal_min_length=election.get_meta_property("min_length"),
                                  legal_max_length=election.get_meta_property("max_length"))
        for voter in election.voters.all():
            profile.append(pbelection.OrdinalBallot([projects[pref.project.project_id] for pref in voter.preference_infos.all()]))
    elif election.ballot_type.name == 'cumulative':
        profile = pbelection.CumulativeProfile(legal_min_length=election.get_meta_property("min_length"),
                                               legal_max_length=election.get_meta_property("max_length"),
                                               legal_min_score=election.get_meta_property("min_points"),
                                               legal_max_score=election.get_meta_property("max_points"),
                                               legal_min_total_score=election.get_meta_property("min_sum_points"),
                                               legal_max_total_score=election.get_meta_property("max_sum_points"))
        for voter in election.voters.all():
            profile.append(pbelection.CumulativeBallot({projects[pref.project.project_id]: pref.preference_strength for pref in voter.preference_infos.all()}))
    elif election.ballot_type.name == 'cardinal':
        profile = pbelection.CardinalProfile(legal_min_length=election.get_meta_property("min_length"),
                                             legal_max_length=election.get_meta_property("max_length"),
                                             legal_min_score=election.get_meta_property("min_points"),
                                             legal_max_score=election.get_meta_property("max_points"))
        for voter in election.voters.all():
            profile.append(pbelection.CardinalBallot({projects[pref.project.project_id]: pref.preference_strength for pref in voter.preference_infos.all()}))

    return instance, profile
