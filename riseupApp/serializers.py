from rest_framework import serializers
from .models import *

class ImagePathSerializer(serializers.Serializer):
    image_path = serializers.CharField()

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'

class ResumeInsightsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeInsights
        fields = '__all__'