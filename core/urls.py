from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # RegisterTeacherView,
    # RegisterStudentView,
    TeacherViewSet,
    StudentViewSet,
    StudentByTeacherViewSet,
    CustomLoginView,
    AdminTeacherViewSet,
    TeacherSelfUpdateView,
    export_students_csv,
    export_teachers_csv
)

router = DefaultRouter()
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'mystudents', StudentByTeacherViewSet, basename='teacher-students')
router.register(r'teacher-admin', AdminTeacherViewSet, basename='admin-teacher')

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='custom_login'),
    path('teacher/me/', TeacherSelfUpdateView.as_view(), name='teacher_self_update'),
    path('export/students/', export_students_csv, name='export_students'),
    path('export/teachers/', export_teachers_csv, name='export_teachers'),


    # path('register/teacher/', RegisterTeacherView.as_view(), name='register_teacher'),
    # path('register/student/', RegisterStudentView.as_view(), name='register_student'),
    path('', include(router.urls)),
]
