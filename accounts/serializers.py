from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Verification


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'mobile_no', 'is_admin', 'is_mobile_verified', 'can_submit_articles']
        read_only_fields = ['id', 'is_admin', 'is_mobile_verified']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'mobile_no']

    def create(self, validated_data):
        user = User(username=validated_data['username'], email=validated_data.get('email'))
        user.mobile_no = validated_data.get('mobile_no')
        user.set_password(validated_data['password'])
        user.is_active = True
        user.save()
        return user


class VerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = ['id', 'mobile_no', 'purpose', 'is_verified', 'created_at']
        read_only_fields = ['id', 'is_verified', 'created_at']


