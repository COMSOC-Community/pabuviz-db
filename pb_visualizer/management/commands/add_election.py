from email.policy import default
from time import sleep
from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.db.models import Max
from numpy import delete

import pb_visualizer

from pb_visualizer.models import *

import traceback
import csv
import os
import datetime

import pprint
from pabutools.election.pabulib import parse_pabulib
from pabutools.election import Instance, Profile

# here we can add multiple aliases for each of the vote types, rules and genders


ballot_type_mapping = {
    'approval': ['approval'],
    'ordinal': ['ordinal'],
    'cumulative': ['cumulative'],
    'cardinal': ['scoring', 'cardinal'],
}

ballot_type_objs = {
    ballot_type: BallotType.objects.get(name=ballot_type) for ballot_type in ballot_type_mapping
}

rule_abbreviation_mapping = {
    'greedy_cost': ['greedy_cost', 'greedy'],
    'mes': ['mes'],
}

rule_objs = {
    rule: Rule.objects.get(abbreviation=rule) for rule in rule_abbreviation_mapping
}

gender_mapping = {
    GENDER_MALE: ['male', 'm'],
    GENDER_FEMALE: ['female', 'f', 'k'],
    GENDER_OTHER: ['other', 'o'],
    GENDER_UNKNOWN: ['', '\\n', 'unknown']
}



def raise_missing_data_exception(type, key, additional_info=""):
    raise Exception("Invalid pb file. The following data is missing: " + type +"." + key + ". " + additional_info)

def generate_name(unit, subunit, district, date):
    if unit:
        return unit + (", " + subunit if subunit else "")+ (", " + district if district else "") + (", " + date.strftime('%Y-%m') if date else "")
    else:
        raise_missing_data_exception("election", "unit")

def collect_election_info (instance_pabutools: Instance,
                           num_projects: int,
                           num_votes: int,
                           has_categories: bool, 
                           has_targets: bool, 
                           has_voting_methods: bool, 
                           has_neighborhoods: bool, 
                           verbosity: int = 1):
    election_defaults = {}
    election_meta_data = {}
    # we iterate through the keys of the meta data o f the pabutools election object and translate them for our Election object
    election_info = instance_pabutools.meta

    election_defaults['num_projects'] = num_projects
    election_defaults['num_votes'] = num_votes

    for key in election_info:

        # first the simple fields
        if key in ['name', 'description', 'country', 'unit', 'instance', 'budget',
                   'subunit', 'language', 'edition', 'district', 'comment']:
            election_defaults[key] = election_info[key]

        elif key in ['max_length', 'min_length', 'max_sum_cost', 'min_sum_cost', 'max_points', 'min_points',
                     'max_sum_points', 'min_sum_points', 'default_score']:
            election_meta_data[key] = election_info[key]

        elif key in ['num_projects', 'num_votes']:
            if  election_defaults[key] != int(election_info[key]):
                if verbosity > 0: print("warning: " + key + " does not match the actual number in the file, ignoring the field")

        elif key == 'vote_type':
            for ballot_type in ballot_type_mapping:
                if election_info[key].lower() in ballot_type_mapping[ballot_type]:
                    election_defaults[key] = ballot_type_objs[ballot_type]
                    break
            else:
                raise Exception("Invalid pb file. The vote type should be one of the following: {}. I was given {}.".format(
                    str([ballot_type + ": " + str(ballot_type_mapping[ballot_type]) for ballot_type in ballot_type_mapping]),
                    election_info[key].lower()))

        elif key == 'rule':
            for rule in rule_abbreviation_mapping:
                if election_info[key].lower() in rule_abbreviation_mapping[rule]:
                    election_defaults[key] = rule_objs[rule]
                    break
            else:
                raise Exception("Unknown rule. Rules currently supported by the database are: " + str([rule + ": " + str(rule_abbreviation_mapping[rule]) for rule in rule_abbreviation_mapping]))

        elif key in ['date_begin', 'date_end']:
            election_defaults[key] = datetime.datetime.strptime(election_info[key], "%d.%m.%Y").date()  # TODO: discuss date format

        else:
            if verbosity > 0: print("ignoring unknown key for election data: ", key)


    # we add the fields missing in the data
    election_defaults['has_categories'] = has_categories
    election_defaults['has_targets'] = has_targets
    election_defaults['has_voting_methods'] = has_voting_methods
    election_defaults['has_neighborhoods'] = has_neighborhoods

    election_defaults['is_trivial'] = instance_pabutools.is_trivial()

    if 'name' not in election_defaults:
        election_defaults['name'] = generate_name(election_defaults.get('unit'),
                                                  election_defaults.get('subunit'),
                                                  election_defaults.get('district'),
                                                  election_defaults.get('date_begin')
                                                  )  #TODO: come up with better automated naming
    
    # we check that all obligatory fields are present
    for field in Election._meta.get_fields():
        if (not field.auto_created 
            and not field.blank
            and not field.has_default()
            and field.name not in election_defaults): 
                # these fields we will add manually later
                if field.name not in ['modification_date']:
                    raise_missing_data_exception('election', field.name)
    
    if election_defaults['ballot_type'].name == 'cumulative':
        if 'max_sum_points' not in election_meta_data:
            raise_missing_data_exception('cumulative election',
                                         'max_sum_points', 
                                         "If there is no upper limit for the number of points every voter can distribute, please use the 'scoring'/'cardinal' vote type.")

    return {
        'defaults': election_defaults,
        'meta_data': election_meta_data
    }



def collect_projects_info(instance_pabutools: Instance,
                          verbosity: int = 1):
    projects_defaults = {}
    projects_foreign_keys = {}

    # containers for the projects/category/target names and the model objects
    categories_set, targets_set = set(), set()
    projects_selected = []

    unknown_keys = []

    # we iterate through the keys of the file and translate them for our Project objects
    for project in instance_pabutools:
        project_defaults = {}
        project_foreign_keys = {}
        project_info = instance_pabutools.project_meta[project]
        for key in project_info:
            if key in ['project_id', 'cost', 'name']:
                project_defaults[key] = project_info[key]
            elif key == 'selected':
                if project_info[key] == '1':
                    projects_selected.append(project.name)    # TODO: remove
            elif key in ['categories', 'targets', 'name']: # skipping redundant information
                continue
            else:
                if key not in unknown_keys and key != 'votes':
                    unknown_keys.append(key)
                    if verbosity > 0: print("ignoring unknown key for project data: ", key)


        for field in Project._meta.get_fields():
            if (not field.auto_created 
                and not field.blank
                and not field.has_default()
                and field.name not in project_defaults): 
                    if field.name not in ['election']:
                        raise_missing_data_exception('project', field.name)
        
        categories_set.update(project.categories)
        project_foreign_keys['categories'] = project.categories
            
        targets_set.update(project.targets)
        project_foreign_keys['targets'] = project.targets

        projects_defaults[project.name] = project_defaults
        projects_foreign_keys[project.name] = project_foreign_keys

    return {
        'projects_defaults': projects_defaults,
        'projects_foreign_keys': projects_foreign_keys,
        'categories_set': categories_set,
        'targets_set': targets_set,
        'projects_selected': projects_selected
    }

def collect_voters_info(profile_pabutools: Profile,
                        ballot_type: str,
                        verbosity: int = 1):
    voters_defaults = {}
    voters_foreign_keys = {}
    # containers for the voting methods model objects
    voting_methods_set = set()
    neighborhoods_set = set()

    unknown_keys = []
    # we iterate through the keys of the file and translate them for our Voter objects


    for profile in profile_pabutools:
        voter_defaults = {}
        voter_foreign_keys = {}
        voter_info = profile.meta

        # add info of the votes
        voter_foreign_keys['votes'] = {}
        for (index, project) in enumerate(profile):
            if ballot_type == 'approval':
                voter_foreign_keys['votes'][project] = 1
            if ballot_type == 'ordinal':
                voter_foreign_keys['votes'][project] = len(profile) - index
            if ballot_type in ['cumulative', 'cardinal']:
                voter_foreign_keys['votes'][project] = profile[project]

        # add info of voters
        for key in voter_info:
            
            if key == 'voter_id':
                voter_defaults[key] = voter_info[key]
            elif key == 'age':
                if voter_info[key] != "":
                    voter_defaults[key] = voter_info[key]
            elif key == 'sex':
                for gender in gender_mapping:
                    if voter_info[key].lower() in gender_mapping[gender]:
                        voter_defaults["gender"] = gender
                        break
                else:
                    raise Exception("Invalid pb file. The gender should be one of the following: {}. I was given {}".format(
                        str([gender + ": " + str(gender_mapping[gender]) for gender in gender_mapping]),
                        voter_info[key].lower()
                    ))

            elif key == 'voting_method':
                voting_methods_set.add(voter_info[key])
                voter_foreign_keys[key] = voter_info[key]

            elif key == 'neighborhood':
                neighborhoods_set.add(voter_info[key])
                voter_foreign_keys[key] = voter_info[key]

            else:
                if key not in unknown_keys and key != 'vote':
                    unknown_keys.append(key)
                    if verbosity > 0: print("ignoring unknown key for voter data: ", key)



        voters_defaults[voter_info['voter_id']] = voter_defaults
        voters_foreign_keys[voter_info['voter_id']] = voter_foreign_keys
        
        for field in Voter._meta.get_fields():
            if (not field.auto_created 
                and not field.blank
                and not field.has_default()
                and field.name not in voters_defaults[voter_info['voter_id']]
                and field.name not in voters_foreign_keys[voter_info['voter_id']]): 
                    if field.name not in ['election',
                                          'votes']:
                        raise_missing_data_exception('vote', field.name)
    
    return {
        'voters_defaults': voters_defaults,
        'voters_foreign_keys': voters_foreign_keys,
        'voting_methods_set': voting_methods_set,
        'neighborhoods_set': neighborhoods_set
    }


def add_dataset(file_path: str, 
                overwrite: bool,
                verbosity: int = 1):
    # We read and parse the file
    # election_info, projects_info, voters_info = parse_pb_file(file_path)
    if verbosity > 1: print("parsing file...")
    instance_pabutools, profile_pabutools = parse_pabulib(file_path)
    ballot_type = instance_pabutools.meta['vote_type']
    if ballot_type == None:
        raise_missing_data_exception('election', 'vote_type')

    if verbosity > 1: print("preparing data...")
    # We construct the defaults dictionary for each model object we want to create
    # the foreign_keys dicts hold the ids of referenced objects
    projects_info = collect_projects_info(instance_pabutools, verbosity)
    voters_info = collect_voters_info(profile_pabutools, ballot_type, verbosity)
    election_info = collect_election_info(
        instance_pabutools,
        len(projects_info['projects_defaults']),
        len(voters_info['voters_defaults']),
        len(projects_info['categories_set']) > 0,
        len(projects_info['targets_set']) > 0,
        len(voters_info['voting_methods_set']) > 0,
        len(voters_info['neighborhoods_set']) > 0,
        verbosity
    )

    if verbosity > 1: print("collecting references...")
    
    # create election object
    election_query = Election.objects.filter(name=election_info['defaults']['name'])
    if election_query.exists():
        if overwrite:
            if verbosity > 1: print("removing existing election...")
            election_query.delete()
        else:
            raise Exception("Election with same name already exists")


    if verbosity > 1: print("creating election object...")
    election_obj = Election.objects.create(**election_info['defaults'])

    # create election data properties
    for metadata in election_info['meta_data']:
        election_metadata_obj = ElectionMetadata.objects.get(short_name=metadata)
        if election_info['defaults']['ballot_type'] in election_metadata_obj.applies_to.all():
            ElectionDataProperty.objects.create(election=election_obj,
                                                metadata=election_metadata_obj,
                                                value=election_info['meta_data'][metadata])
        else:
            if verbosity > 0: print("Ignoring field " + metadata + " for vote type " + election_info['defaults']['ballot_type'].name)

    # create containers for all created objects and fill them
    categories_obj, targets_obj, voting_methods_obj, neighborhoods_obj, projects_obj = {}, {}, {}, {}, {}

    for category in projects_info['categories_set']:
        categories_obj[category] = Category.objects.create(election=election_obj,
                                                           name=category)
    for target in projects_info['targets_set']:
        targets_obj[target] = Target.objects.create(election=election_obj,
                                                    name=target)
    for voting_method in voters_info['voting_methods_set']:
        voting_methods_obj[voting_method] = VotingMethod.objects.create(election=election_obj,
                                                                        name=voting_method)
    for neighborhood in voters_info['neighborhoods_set']:
        neighborhoods_obj[neighborhood] = Neighborhood.objects.create(election=election_obj,
                                                                      name=neighborhood)
    if verbosity > 1: print("creating project objects...")
    # create project objects
    for index, project_id in enumerate(projects_info['projects_defaults']):
        # if verbosity > 1: print(str(index) + "/" + str(len(projects_defaults)), end="\r")
        project_obj = Project.objects.create(election=election_obj,
                                             **projects_info['projects_defaults'][project_id])
        
        if 'categories' in projects_info['projects_foreign_keys'][project_id]:
            project_obj.categories.set([categories_obj[category] for category in projects_info['projects_foreign_keys'][project_id]['categories']])

        if 'targets' in projects_info['projects_foreign_keys'][project_id]:
            project_obj.targets.set([targets_obj[target] for target in projects_info['projects_foreign_keys'][project_id]['targets']])

        projects_obj[project_id] = project_obj

    if verbosity > 1: print("creating voter objects...")
    # create voter objects
    voters_objs = []
    pref_info_objs = []
    if verbosity > 1: print("~ 0 %  ", end="\r")
    for voter_id in voters_info['voters_defaults']:

        if 'voting_method' in voters_info['voters_foreign_keys'][voter_id]:
            voters_info['voters_defaults'][voter_id]['voting_method'] = voting_methods_obj[voters_info['voters_foreign_keys'][voter_id]['voting_method']]
        
        if 'neighborhood' in voters_info['voters_foreign_keys'][voter_id]:
            voters_info['voters_defaults'][voter_id]['neighborhood'] = neighborhoods_obj[voters_info['voters_foreign_keys'][voter_id]['neighborhood']]
        
        voter_obj = Voter(election=election_obj, **voters_info['voters_defaults'][voter_id])
        for project in voters_info['voters_foreign_keys'][voter_id]['votes']:
            pref_info_objs.append(PreferenceInfo(voter=voter_obj,
                                                 project=projects_obj[project],
                                                 preference_strength=voters_info['voters_foreign_keys'][voter_id]['votes'][project]))
        voters_objs.append(voter_obj)

    if verbosity > 1: print("~10 %  ", end="\r")
    Voter.objects.bulk_create(voters_objs)
    
    if verbosity > 1: print("~50 %  ", end="\r")
    PreferenceInfo.objects.bulk_create(pref_info_objs)
        
    return


class Command(BaseCommand):
    help = "Add .pb file to database"

    def add_arguments(self, parser):
        parser.add_argument('-d', nargs='*', type=str) # TODO: implement functionality and test
        parser.add_argument('-f', nargs='*', type=str)
        parser.add_argument('-o', '--overwrite', nargs='?', type=bool, const=True, default=False)
        # parser.add_argument('--all', action='store_true')

    def handle(self, *args, **options):
        if not options['d'] and not options['f']:
            print("ERROR: you need to pass an input argument: either -d for a directory of -f for a single file.")
            return
        if options['f']:
            for file_path in options['f']:
                if os.path.splitext(file_path)[1] != ".pb":
                    print("ERROR: the argument -f should point to a .pb file, and {} does not look like one.".format(
                        file_path))
                    return
        if options['d']:
            for dir_path in options['d']:
                if not os.path.isdir(dir_path):
                    print("ERROR: the argument -d should point to a directory, and {} does not look like one.".format(
                        dir_path))
                    return



        log = []
        new_log_num = 0

        try:
            # Initializing the log
            new_log_num = Log.objects.filter(log_type='add_dataset').aggregate(Max('log_num'))['log_num__max']
            if new_log_num is None:
                new_log_num = 0
            else:
                new_log_num += 1

            # Looking for the data folder, creating it if it's not there
            data_dir = finders.find('data')
            if not data_dir:
                try:
                    data_dir = os.path.join(os.path.dirname(pb_visualizer.__file__), 'static', 'data')
                    os.makedirs(data_dir)
                except FileExistsError:
                    pass


            # Starting the log
            log = ["<h4> Adding dataset #" + str(new_log_num) + " - " + str(timezone.now()) + "</h4>\n",
                   "<ul>\n\t<li>args : " + str(args) + "</li>\n\t<li>options : " + str(options) +
                   "</li>\n</ul>\n"]

            # If directory, add all files to the '-f' option
            if options['d']:
                if not options['f']:
                    options['f'] = []
                for dir_path in options['d']:
                    for filename in os.listdir(dir_path):
                        if filename.endswith(".pb"):
                            options['f'].append(os.path.join(dir_path, filename))

            # Starting the real stuff
            log.append("<p>Adding datasets</p>\n<ul>\n")
            start_time = timezone.now()
            for i, file_path in enumerate(options['f']):

                # We only consider pb files
                if os.path.splitext(file_path)[1] == '.pb':
                    # Let's work on the dataset
                    file_name = os.path.basename(file_path)
                    if options['verbosity'] > 0: print("Adding dataset {} ({}/{})".format(str(file_name), str(i+1), str(len(options['f']))))
                    log.append("\n\t<li>Dataset " + str(file_name) + "... ")
                    try:
                        # Actually adding the dataset
                        add_dataset(file_path, options['overwrite'], options['verbosity'])
                        log.append(" ... done.</li>\n")
                    except Exception as e:
                        # If something happened, we log it and move on
                        log.append("</li>\n</ul>\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) +
                                   "	</strong></p>\n<ul>")
                        print(traceback.format_exc())
                        print(e)


            # Finalizing the log
            log.append("</ul>\n<p>The datasets have been successfully added in ")
            log.append(str((timezone.now() - start_time).total_seconds() / 60))
            log.append(" minutes.</p>")

            # Collecting the statics once everything has been done
            if options['verbosity'] > 0: print("Finished, collecting statics")
            management.call_command('collectstatic', no_input=False, verbosity=options['verbosity']-1)
        except Exception as e:
            # If anything happened during the execution, we log it and move on
            log.append("\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
            print(traceback.format_exc())
            print(e)
        finally:
            # In any cases, we save the log
            Log.objects.create(
                log=''.join(log),
                log_type='add_dataset',
                log_num=new_log_num,
                publication_date=timezone.now())
