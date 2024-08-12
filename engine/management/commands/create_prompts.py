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
        full_path = os.path.join(app_path, 'prompts.json')

        if not os.path.isfile(full_path):
            self.stderr.write(self.style.ERROR(f"File {full_path} does not exist."))
            return

        with open(full_path, 'r') as file:
            data = json.load(file)

        self.import_data(data)

    def import_data(self, data):
        for category_name, category_data in data.items():
    
            category, created = EngineCategory.objects.get_or_create(
                name=category_name,
                defaults={'prompt': category_data.get('prompt', '')}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created EngineCategory: {category_name}"))
            else:
                self.stdout.write(f"EngineCategory already exists: {category_name}")

            for engine in category_data.get('engines', []):
                for engine_name, engine_description in engine.items():
                   Engine.objects.update_or_create(
                    category=category,
                    name=engine_name,
                    defaults={'prompt': engine_description}
                )
                self.stdout.write(self.style.SUCCESS(f"Created/Updated Engine: {engine_name} for Category: {category_name}"))