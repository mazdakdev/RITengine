from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
from engine.models import Message, Engine
from .models import Vote
from RITengine.exceptions import CustomAPIException

class LikeDislikeView(APIView):
    """
    Handles liking or disliking a message, associating the vote with the specified engines.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id, vote_type):
        user = request.user

        if vote_type not in [Vote.LIKE, Vote.DISLIKE]:
            raise CustomAPIException("Invalid vote type.")

        message = get_object_or_404(Message, id=message_id)

        existing_vote = Vote.objects.filter(user=user, message=message).first()
        if existing_vote:
            raise CustomAPIException("You have already voted for this message.")

        vote = Vote.objects.create(user=user, message=message, vote_type=vote_type)
        vote.save()

        return Response({"status": "Vote cast."}, status=201)
