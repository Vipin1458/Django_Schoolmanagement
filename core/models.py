from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return self.username


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    subject_specialization = models.CharField(max_length=100)
    date_of_joining = models.DateField()
    status = models.IntegerField(default=0)  # e.g., 0 = active, 1 = inactive

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    grade = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    admission_date = models.DateField()
    status = models.IntegerField(default=0)  # e.g., 0 = active, 1 = inactive
    assigned_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.roll_number}"
