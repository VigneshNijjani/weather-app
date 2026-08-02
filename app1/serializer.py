from rest_framework import serializers
from .models import wheater

class wheaterserializer(serializers.ModelSerializer):
    class Meta:
        fields="__all__"
        model=wheater