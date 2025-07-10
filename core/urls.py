from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterTeacherView,
    RegisterStudentView,
    TeacherViewSet,
    StudentViewSet,
    StudentByTeacherViewSet,
    CustomLoginView,
    AdminTeacherViewSet
)

router = DefaultRouter()
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'mystudents', StudentByTeacherViewSet, basename='teacher-students')
router.register(r'teacher-admin', AdminTeacherViewSet, basename='admin-teacher')

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='custom_login'),
    path('register/teacher/', RegisterTeacherView.as_view(), name='register_teacher'),
    path('register/student/', RegisterStudentView.as_view(), name='register_student'),
    path('', include(router.urls)),
]
