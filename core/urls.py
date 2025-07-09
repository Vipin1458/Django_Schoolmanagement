from django.urls import path
from .views import (
    RegisterTeacherView,
    RegisterStudentView,
    TeacherListView,
    StudentListView,
    StudentsByTeacherView,
    CustomLoginView
)


urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='register_teacher'),
    path('register/teacher/', RegisterTeacherView.as_view(), name='register_teacher'),
    path('register/student/', RegisterStudentView.as_view(), name='register_student'),
    path('teachers/', TeacherListView.as_view(), name='teacher_list'),
    path('students/', StudentListView.as_view(), name='student_list'),
    path('students/teacher/<int:teacher_id>/', StudentsByTeacherView.as_view(), name='students_by_teacher')
]