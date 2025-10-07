from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    mobile_no = models.CharField(max_length=20, blank=True, null=True, unique=True)
    is_admin = models.BooleanField(default=False)
    is_mobile_verified = models.BooleanField(default=False)
    can_submit_articles = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.username


class Verification(models.Model):
    PURPOSE_CHOICES = (
        ('register', 'Register'),
        ('guest_comment', 'Guest Comment'),
        ('guest_article', 'Guest Article'),
    )

    mobile_no = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.mobile_no} {self.purpose} verified={self.is_verified}"


