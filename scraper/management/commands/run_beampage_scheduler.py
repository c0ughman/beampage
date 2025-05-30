from django.core.management.base import BaseCommand
from scraper.workflow import run_workflow_command
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run Beampage workflow scheduler for Heroku'

    def add_arguments(self, parser):
        parser.add_argument(
            '--page',
            type=str,
            help='Specific page to process (optional)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=3600,  # 1 hour
            help='Interval between runs in seconds (default: 3600)',
        )

    def handle(self, *args, **options):
        page_name = options.get('page')
        interval = options.get('interval')
        
        logger.info(f"Starting Beampage scheduler (interval: {interval}s)")
        
        while True:
            try:
                logger.info("Running Beampage workflow...")
                run_workflow_command(page_name)
                logger.info(f"Workflow completed. Sleeping for {interval} seconds...")
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(60)  # Wait 1 minute before retrying 