from django.contrib import admin

# Register your models here.
from .models import Problem, TestCase

admin.site.register(Problem)
admin.site.register(TestCase)