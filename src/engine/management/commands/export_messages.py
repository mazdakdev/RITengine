import csv
from django.core.management.base import BaseCommand
from engine.models import Message
from django.contrib.auth import get_user_model

User = get_user_model

class Command(BaseCommand):
    help = 'Export messages for certain users to a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('user_ids', nargs='+', type=int, help='List of user IDs to export messages for')

        parser.add_argument(
            '--output',
            type=str,
            help='The output file where messages will be exported (e.g., messages.csv)',
        )

    def handle(self, *args, **kwargs):
        user_ids = kwargs['user_ids']
        output_file = kwargs.get('output', 'messages.csv')

        messages = Message.objects.filter(chat__user__id__in=user_ids)

        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['user_id', 'message_content', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for message in messages:
                writer.writerow({
                    'user_id': message.chat.user.id,
                    'message_content': message.text,
                    'timestamp': message.timestamp,
                })

        self.stdout.write(self.style.SUCCESS(f'Messages exported to {output_file}'))
