from rest_framework import serializers
from django.contrib.auth import get_user_model

class CustomerSerializer(serializers.Serializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name', 'email']