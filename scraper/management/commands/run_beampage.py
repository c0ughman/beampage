"""
Django management command to run the Beampage workflow
"""

from django.core.management.base import BaseCommand, CommandError
from scraper.workflow import run_workflow_command


class Command(BaseCommand):
    help = 'Run the Beampage Instagram scraping and reposting workflow'

    def add_arguments(self, parser):
        parser.add_argument(
            'page_name',
            nargs='?',
            help='Name of the page to process (optional). Use "list" to see configured pages, "status" for recent results.'
        )

    def handle(self, *args, **options):
        page_name = options.get('page_name')
        
        try:
            run_workflow_command(page_name)
        except Exception as e:
            raise CommandError(f'Workflow failed: {e}') 