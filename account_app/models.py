from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    affiliation = models.CharField(max_length=255, blank=False, null=False)
    reason = models.TextField(max_length=1000, default='', blank=True)

    def __str__(self):
        return '{} - {}'.format(self.user, self.affiliation)
