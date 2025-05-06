from django.db import models

# Create your models here.
class UsersCount(models.Model):
    path = models.TextField(blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    counter = models.PositiveIntegerField()

    def __str__(self):
        return f"User Count is at {self.counter} "

