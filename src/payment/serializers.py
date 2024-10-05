from rest_framework import serializers
from .models import Plan, PlanPrice
from rest_framework.exceptions import NotFound

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price', 'interval_count', 'currency', 'messages_per_day', 'projects_total', 'bookmarks_total', 'interval']


class SubscriptionSerializer(serializers.Serializer):
    plan_price_id = serializers.IntegerField()

    def get_price_id(self):
        plan_price_id = self.validated_data['plan_price_id']
        try:
            plan_price = PlanPrice.objects.get(id=plan_price_id)
        except Plan.DoesNotExist:
            raise NotFound("Plan not found")
        return plan_price.stripe_price_id
