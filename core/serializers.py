from rest_framework import serializers
from .models import Theme


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=140)
    message = serializers.CharField()


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = ['id', 'key', 'name', 'is_active']
        read_only_fields = ['id']


