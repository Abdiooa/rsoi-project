from rest_framework import serializers
from .models import UserLoyalty
import uuid

class UserLoyaltySerializer(serializers.ModelSerializer):
    class Meta:
        model=UserLoyalty
        fields='__all__'