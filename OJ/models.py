from distutils.command.build_scripts import first_line_re
import importlib.util
from django.db import models
from froala_editor.fields import FroalaField


###############################################################################################################################


class Problem(models.Model):
    TOUGHNESS = (("Easy", "Easy"), ("Medium", "Medium"), ("Tough", "Tough"))
    STATUS = (("Unsolved", "Unsolved"), ("Solved", "Solved"))
    name = models.CharField(max_length=100, default="")
    description = models.CharField(max_length=1000, default="")
    difficulty = models.CharField(max_length=10, choices=TOUGHNESS)
    time_limit = models.IntegerField(default=2, help_text="in seconds")
    memory_limit = models.IntegerField(default=128, help_text="in kb")

    def __str__(self):
        return self.name


###############################################################################################################################


class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    input = models.TextField()
    output = models.TextField()

    def __str__(self):
        return ("TC: " + str(self.id) + " for Problem: " + str(self.problem))