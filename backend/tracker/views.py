from rest_framework import viewsets
from .models import UsageLog, Nudge
from .serializers import UsageLogSerializer, NudgeSerializer

class UsageLogViewSet(viewsets.ModelViewSet):
    queryset = UsageLog.objects.all()
    serializer_class = UsageLogSerializer

class NudgeViewSet(viewsets.ModelViewSet):
    queryset = Nudge.objects.all()
    serializer_class = NudgeSerializer