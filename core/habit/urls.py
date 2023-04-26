from django.urls import path, include
from rest_framework.routers import DefaultRouter

from habit.views import HabitViewSet, CreateTrackingView

router = DefaultRouter()
router.register(r'habits', HabitViewSet, basename='habit')

urlpatterns = [
    path('', include(router.urls)),
    path('trackings/', CreateTrackingView.as_view(), name='create_tracking')
]
