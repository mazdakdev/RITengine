import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from engine.models import EngineCategory, Engine
from django.apps import apps

class Command(BaseCommand):
    help = 'Import engine categories and engines from a JSON file'

    def handle(self, *args, **options):
        app_path = apps.get_app_config('engine').path
        full_path = os.path.join(app_path, 'management/commands/prompts.json')

        if not os.path.isfile(full_path):
            self.stderr.write(self.style.ERROR(f"File {full_path} does not exist."))
            return

        with open(full_path, 'r') as file:
            data = json.load(file)

        self.import_data(data)

    def import_data(self, data):
        for category_name, category_data in data.items():
            category_prompt = category_data.get('prompt', '')
            is_default = category_data.get('is_default', False)

            # Create or update the EngineCategory with the is_default field
            category, created = EngineCategory.objects.update_or_create(
                name=category_name,
                defaults={'prompt': category_prompt, 'is_default': is_default}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created EngineCategory: {category_name}"))
            else:
                self.stdout.write(f"EngineCategory already exists: {category_name}")

            for engine_data in category_data.get('engines', []):
                for engine_name, engine_info in engine_data.items():
                    engine_prompt = engine_info.get('prompt', None)
                    external_service = engine_info.get('external_service', None)

                    Engine.objects.update_or_create(
                        category=category,
                        name=engine_name,
                        defaults={'prompt': engine_prompt, 'external_service': external_service}
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created/Updated Engine: {engine_name} for Category: {category_name}"))
