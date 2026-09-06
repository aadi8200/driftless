from rest_framework.routers import DefaultRouter
from .views import UsageLogViewSet, NudgeViewSet

router = DefaultRouter()
router.register('usage-logs', UsageLogViewSet)
router.register('nudges', NudgeViewSet)

urlpatterns = router.urls