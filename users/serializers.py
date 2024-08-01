import os

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import CustomUser
from files.serializers import CustomFileSerializer


class UsersListSerializer(serializers.ModelSerializer):
    #password = serializers.CharField(write_only=True)
    # files = CustomFileSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'is_admin']


class UsersSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    files = CustomFileSerializer(many=True, read_only=True)

    class Meta:
       model = CustomUser
       fields = ['id', 'username', 'full_name', 'email', 'password', 'is_admin', 'user_storage_path', 'files',]

    def create(self, validated_data):
        print(validated_data['password'],"validated_data['password']")
        validated_data['user_storage_path'] = os.path.join(settings.STORAGE_DIR, validated_data['username'])
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_admin=False,
            user_storage_path=validated_data['user_storage_path']
        )
        return user

    def validate(self, data):
        if not data['username'].isalnum():
            raise serializers.ValidationError({'username': 'Username must contain only alphanumeric characters.'})
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({'username': 'Username already exists.'})
        return data


# для обновления / изменения данных пользователя
class UserUpdateSerializer(serializers.ModelSerializer):
        class Meta:
            model = CustomUser
            fields = ['username', 'full_name', 'email']
