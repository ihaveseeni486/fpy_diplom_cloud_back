from rest_framework import serializers

from .models import CustomFile

class CustomFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFile
        fields = ['id', 'file_name', 'file_size', 'upload_date', 'last_download_date', 'comment', 'file_path',
                          'special_link', ]