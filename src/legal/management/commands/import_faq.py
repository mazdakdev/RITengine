import json
import os
from django.core.management.base import BaseCommand
from legal.models import FaqDocument
from django.apps import apps

class Command(BaseCommand):
    help = 'Import FAQ documents from a JSON file'

    def handle(self, *args, **options):
        app_path = apps.get_app_config('legal').path
        full_path = os.path.join(app_path, 'management/commands/faq.json')

        if not os.path.isfile(full_path):
            self.stderr.write(self.style.ERROR(f"File {full_path} does not exist."))
            return

        with open(full_path, 'r') as file:
            data = json.load(file)

        self.import_data(data)

    def import_data(self, data):
        for question, answer in data.items():

            FaqDocument.objects.update_or_create(
                question=question,
                answer=answer
            )
            self.stdout.write(self.style.SUCCESS(f"Created/Updated FAQ Document: {question}"))