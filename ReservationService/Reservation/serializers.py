from dataclasses import fields
from rest_framework import serializers
from .models import Hotel, Reservation
import uuid

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Reservation
        fields='__all__'

class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model=Hotel
        fields='__all__'
    
    def create(self,validated_data):
        validated_data.pop('role',None)
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance
