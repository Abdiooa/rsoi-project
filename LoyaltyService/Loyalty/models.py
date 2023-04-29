from django.db import models
import uuid

class UserLoyalty(models.Model):
    username=models.CharField(max_length=200,unique=True)
    reservationCount=models.IntegerField(default=0)
    status=models.CharField(max_length=10,default='BRONZE')
    discount=models.IntegerField(default=0)
    balance = models.IntegerField(default=0)