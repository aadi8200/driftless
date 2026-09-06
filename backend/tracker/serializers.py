from rest_framework import serializers
from .models import UsageLog, Nudge

class UsageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageLog
        fields = '__all__'

class NudgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nudge
        fields = '__all__'