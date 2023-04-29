from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.core.validators import EmailValidator


class Users(AbstractUser):
    user_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    role = models.CharField(max_length=50)
    email = models.EmailField(max_length=255, unique=True, validators=[EmailValidator()])
    password =models.CharField(max_length=255)
    username = models.CharField(unique=True,max_length=255)
    name = models.CharField(max_length=255)
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'username'