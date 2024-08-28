from django.db.models import Count, Case, When, IntegerField
from engine.models import Engine, Message
from django.db.models.functions import TruncDay
from .models import Vote
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils.dateformat import DateFormat

def get_engine_performance():
    return Engine.objects.annotate(
        total_likes=Count(Case(
            When(messages__votes__vote_type=Vote.LIKE, then=1),
            output_field=IntegerField()
        )),

        total_dislikes=Count(Case(
            When(messages__votes__vote_type=Vote.DISLIKE, then=1),
            output_field=IntegerField()
        ))
    ).values('name', 'total_likes', 'total_dislikes')

def get_engine_performance_over_time():
    data = Engine.objects.annotate(
        date=TruncDay('messages__votes__created_at'),
        likes=Count(Case(
            When(messages__votes__vote_type=Vote.LIKE, then=1),
            output_field=IntegerField()
        )),
        dislikes=Count(Case(
            When(messages__votes__vote_type=Vote.DISLIKE, then=1),
            output_field=IntegerField()
        ))
    ).values('name', 'date', 'likes', 'dislikes').order_by('date')

    # Convert queryset to a list of dictionaries and handle None or datetime values
    performance_data = list(data)
    for entry in performance_data:
        if entry['date'] is None:
            entry['date'] = ''
        else:
            entry['date'] = DateFormat(entry['date']).format('Y-m-d')

    return performance_data
