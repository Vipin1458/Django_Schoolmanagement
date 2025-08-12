# chat/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ConversationViewSet

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversations")

urlpatterns = [
    path("api/", include(router.urls)),
]
