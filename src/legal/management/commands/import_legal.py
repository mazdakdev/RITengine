import json
import os
from django.core.management.base import BaseCommand
from legal.models import LegalDocument
from django.apps import apps

class Command(BaseCommand):
    help = 'Import legal documents from a JSON file'

    def handle(self, *args, **options):
        app_path = apps.get_app_config('legal').path
        full_path = os.path.join(app_path, 'management/commands/legal.json')

        if not os.path.isfile(full_path):
            self.stderr.write(self.style.ERROR(f"File {full_path} does not exist."))
            return

        with open(full_path, 'r') as file:
            data = json.load(file)

        self.import_data(data)

    def import_data(self, data):
        for doc_type, doc_data in data.items():
            content = doc_data.get('content', '')

            LegalDocument.objects.update_or_create(
                doc_type=doc_type,
                defaults={
                    'content': content
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Created/Updated Legal Document: {doc_type}"))