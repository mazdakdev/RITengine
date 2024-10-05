from rest_framework import serializers
from .models import Plan
from rest_framework.exceptions import NotFound

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price', 'interval_count', 'currency', 'messages_per_day', 'projects_total', 'bookmarks_total', 'interval']


class SubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()

    def get_price_id(self):
        plan_id = self.validated_data['plan_id']
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            raise NotFound("Plan not found")
        return plan.stripe_price_id
