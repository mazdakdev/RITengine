from django.db.models import Count, Case, When, IntegerField
from .models import Vote
from engine.models import Engine, Message

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
