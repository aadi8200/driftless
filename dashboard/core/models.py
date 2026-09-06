from django.db import models
from django.contrib.auth.models import User


class UsageLog(models.Model):
    """
    Stores the total time (seconds) a user spent on a website on a given date.
    The unique_together constraint ensures we accumulate, not duplicate,
    when the extension POSTs multiple times per day.
    """
    user               = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_logs')
    website_url        = models.CharField(max_length=255)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    date               = models.DateField()
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'website_url', 'date')
        ordering        = ['-date', 'website_url']
        indexes         = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        mins = self.time_spent_seconds // 60
        return f'{self.user.username} | {self.website_url} | {self.date} | {mins}m'