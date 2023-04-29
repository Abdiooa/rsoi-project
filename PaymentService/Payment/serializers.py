from rest_framework import serializers
from .models import Payment
import uuid

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Payment
        fields='__all__'