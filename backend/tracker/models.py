from django.db import models

class UsageLog(models.Model):
    user_id = models.CharField(max_length=100, default="test_user")
    tab_url = models.URLField(max_length=500)
    tab_title = models.CharField(max_length=255, blank=True)
    duration_seconds = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tab_title} - {self.duration_seconds}s"


class Nudge(models.Model):
    user_id = models.CharField(max_length=100, default="test_user")
    message = models.CharField(max_length=255)
    triggered_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)