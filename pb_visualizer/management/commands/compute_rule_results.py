from django.core.management import BaseCommand
from pabutools import fractions

from pb_visualizer.management.commands.compute_properties import print_if_verbose
from pb_visualizer.models import Election


def compute_rule_results(election_names=None,
                       rules=None,
                       exact=False,
                       overwrite: bool = False,
                       verbosity=1):
    election_query = Election.objects.all()
    if election_names != None:
        election_query = election_query.filter(name__in=election_names)
    if not exact:
        fractions.FRACTION = 'float'
    n_elections = len(election_query)
    for index, election_obj in enumerate(election_query):
        print_if_verbose("Computing properties of election {}/{}: {}".format(index + 1, n_elections, election_obj.name),
                         1, verbosity, persist=True)
        election_parser = LazyElectionParser(election_obj, verbosity)

        print_if_verbose("basic election properties...", 1, verbosity)
        compute_election_properties(election_parser, overwrite=overwrite, verbosity=verbosity)

        if rules == None or len(rules) > 0:
            print_if_verbose("rule results...", 1, verbosity)
            compute_election_results(election_parser, rules, overwrite=overwrite, verbosity=verbosity)

        if rule_properties == None or len(rule_properties) > 0:
            print_if_verbose("rule result properties...", 1, verbosity)
            compute_rule_result_properties(election_parser, rule_properties, overwrite=overwrite, verbosity=verbosity)

class Command(BaseCommand):
    help = "compute all properties, rules and rule result properties for the elections in the database"

    def add_arguments(self, parser):
        parser.add_argument('-e', '--election_names', nargs='*', type=str, default=None,
                            help="Give a list of election names for which you want to compute properties.")
        parser.add_argument('-r', '--rules', nargs='*', type=str, default=None,
                            help="Give a list of rules for which you want to the results. Discard option to compute all rules, no parameter to skip the rule computation.")
        parser.add_argument('--exact', nargs='?', type=bool, const=True, default=False,
                            help="Use exact fractions instead of floats for computing results.")
        parser.add_argument('-o', '--overwrite', nargs='?', type=bool, const=True, default=False,
                            help="Overwrite properties that were already computed.")

    def handle(self, *args, **options):
        compute_properties(election_names=options['election_names'],
                           rules=options['rules'],
                           rule_properties=options['rule_properties'],
                           exact=options['exact'],
                           overwrite=options['overwrite'],
                           verbosity=options["verbosity"])