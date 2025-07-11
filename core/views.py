from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,viewsets
from .serializers import TeacherSerializer, StudentSerializer
from .models import Teacher, Student
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from .permissions import IsAdmin, IsTeacher,IsAdminOrSelf
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveUpdateAPIView
import csv
from django.http import HttpResponse
from .serializers import TeacherSelfUpdateSerializer
import logging




# class RegisterTeacherView(APIView):
#     permission_classes = [IsAdmin]

#     def post(self, request):
#         serializer = TeacherSerializer(data=request.data)
#         if serializer.is_valid():
#             teacher = serializer.save()
#             return Response({
#                 "message": "Teacher registered successfully.",
#                 "teacher_id": teacher.id,
#                 "user_id": teacher.user.id
#             }, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class RegisterStudentView(APIView):
#     permission_classes = [IsAdmin]

#     def post(self, request):
#         serializer = StudentSerializer(data=request.data)
#         if serializer.is_valid():
#             student = serializer.save()
#             return Response({
#                 "message": "Student registered successfully.",
#                 "student_id": student.id,
#                 "user_id": student.user.id
#             }, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


logger = logging.getLogger(__name__)
    
class CustomLoginView(APIView):
    permission_classes = []  

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        logger.info(f"Login attempt for username: {username}")
        if not username or not password:
            return Response({"error": "Please provide both username and password."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            logger.error(f"Invalid login for username: {username}")
            return Response({"error": "Invalid credentials."},
                            status=status.HTTP_401_UNAUTHORIZED)
        logger.info(f"Login successful for user: {user.username}")
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }, status=status.HTTP_200_OK)




class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSelf]  # Update here

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Teacher.objects.all()
        elif user.role == 'teacher':
            return Teacher.objects.filter(user=user)
        return Teacher.objects.none()

    def create(self, request, *args, **kwargs):
        logger.info(f"[ADMIN:{request.user.username}] Creating a new teacher")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        teacher = self.get_object()
        logger.info(f"[{request.user.role.upper()}:{request.user.username}] Updating teacher ID {teacher.id}")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        teacher = self.get_object()
        logger.warning(f"[{request.user.role.upper()}:{request.user.username}] Deleting teacher ID {teacher.id}")
        return super().destroy(request, *args, **kwargs)


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSelf]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Student.objects.all()
        elif user.role == 'student':
            return Student.objects.filter(user=user)
        elif user.role == 'teacher':
            return Student.objects.filter(assigned_teacher__user=user)
        return Student.objects.none()

    def create(self, request, *args, **kwargs):
        logger.info(f"[ADMIN:{request.user.username}] Creating a new student")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        student = self.get_object()
        logger.info(f"[ADMIN:{request.user.username}] Updating student ID {student.id}")
        logger.debug(f"Update data: {request.data}")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        student = self.get_object()
        logger.warning(f"[ADMIN:{request.user.username}] Deleting student ID {student.id}")
        return super().destroy(request, *args, **kwargs)
  

# class StudentByTeacherViewSet(viewsets.ReadOnlyModelViewSet):
class StudentByTeacherViewSet(viewsets.ModelViewSet):    
    serializer_class = StudentSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Student.objects.filter(assigned_teacher__user=self.request.user)
    
    def get_object(self):
        obj = super().get_object()
        if obj.assigned_teacher.user != self.request.user:
            raise PermissionDenied("You do not have permission to access this student.")
        return obj

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_data = serializer.data
        
        if getattr(serializer, 'warn_assigned_teacher_change', False):
            response_data['warning'] = "Assigned teacher can only be changed by admin."

        return Response(response_data)


    def perform_create(self, serializer):
        serializer.save(assigned_teacher=self.request.user.teacher)

class AdminTeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAdmin]

    @action(detail=True, methods=['get'], url_path='students')
    def get_students(self, request, pk=None):
        teacher = self.get_object()
        students = Student.objects.filter(assigned_teacher=teacher)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)
    

class TeacherSelfUpdateView(RetrieveUpdateAPIView):
    serializer_class = TeacherSelfUpdateSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_object(self):
        return self.request.user.teacher
    
def export_students_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Grade', 'Phone'])

    for student in Student.objects.select_related('user'):
        writer.writerow([student.id, student.user.username, student.grade, student.phone_number])

    return response

def export_teachers_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="teachers.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Specialization', 'Phone'])

    for teacher in Teacher.objects.select_related('user'):
        writer.writerow([teacher.id, teacher.user.username, teacher.subject_specialization, teacher.phone_number])

    return response