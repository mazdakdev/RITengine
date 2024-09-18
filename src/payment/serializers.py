from rest_framework import serializers

PLAN_NAME_TO_PRICE_ID = {
        'Freelancer': 'price_1Q046NP8Rb86zbnBF7ZKSNDD',
}

class SubscriptionSerializer(serializers.Serializer):
    plan_name = serializers.ChoiceField(choices=list(PLAN_NAME_TO_PRICE_ID.keys()))

    def validate_plan_name(self, value):
        if value not in PLAN_NAME_TO_PRICE_ID:
            raise serializers.ValidationError("Invalid plan name.")
        return value

    def get_price_id(self):
        return PLAN_NAME_TO_PRICE_ID.get(self.validated_data['plan_name'])
