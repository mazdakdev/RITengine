from rest_framework import serializers
from .models import Plan, PlanPrice
from rest_framework.exceptions import NotFound

class PlanPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanPrice
        fields = ['id', 'price', 'interval_count', 'interval', 'currency']

class PlanSerializer(serializers.ModelSerializer):
    prices = PlanPriceSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'messages_limit', 'projects_limit', 'bookmarks_limit', 'prices']

class SubscriptionSerializer(serializers.Serializer):
    price_id = serializers.IntegerField()

    def get_price_id(self):
        price_id = self.validated_data['price_id']
        try:
            plan_price = PlanPrice.objects.get(id=price_id)
        except PlanPrice.DoesNotExist:
            raise NotFound("Plan Price not found")
        return plan_price.stripe_price_id
