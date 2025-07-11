from django.test import TestCase
from django.utils import timezone
from core.models import User, Teacher, Student

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username='teacher1', password='pass1234', role='teacher')
        self.assertEqual(user.username, 'teacher1')
        self.assertEqual(user.role, 'teacher')
        self.assertTrue(user.check_password('pass1234'))

class TeacherModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teachertest', password='pass1234', role='teacher')

    def test_create_teacher(self):
        teacher = Teacher.objects.create(
            user=self.user,
            employee_id='EMP001',
            phone_number='1234567890',
            subject_specialization='Math',
            date_of_joining=timezone.now().date(),
            status=0
        )
        self.assertEqual(teacher.employee_id, 'EMP001')
        self.assertEqual(str(teacher), f"{self.user.get_full_name()} - {teacher.employee_id}")

class StudentModelTest(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(username='teachertest2', password='pass1234', role='teacher')
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            employee_id='EMP002',
            phone_number='9876543210',
            subject_specialization='Science',
            date_of_joining=timezone.now().date()
        )

        self.student_user = User.objects.create_user(username='studenttest', password='pass1234', role='student')

    def test_create_student(self):
        student = Student.objects.create(
            user=self.student_user,
            roll_number='ROLL001',
            phone_number='1122334455',
            grade='10',
            date_of_birth='2008-05-10',
            admission_date='2023-06-01',
            assigned_teacher=self.teacher
        )
        self.assertEqual(student.roll_number, 'ROLL001')
        self.assertEqual(student.assigned_teacher, self.teacher)
        self.assertEqual(str(student), f"{self.student_user.get_full_name()} - {student.roll_number}")
