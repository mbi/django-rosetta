from django.core.management.base import BaseCommand, CommandError
from rosetta.models import RosettaSettings


class Command(BaseCommand):
    help = 'Set system state'

    def add_arguments(self, parser):
        parser.add_argument('value', nargs='+')

    def handle(self, *args, **options):
        for value in options['value']:
            self.stdout.write('Value is %s' % value)
            RosettaSettings.instance().set_readonly(value == "True")

        self.stdout.write('System state is "%s" now' % RosettaSettings.instance().readonly)