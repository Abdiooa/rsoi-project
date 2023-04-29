from django.db import models
import uuid

class Payment(models.Model):
    paymentUid=models.UUIDField(unique=True,default=uuid.uuid4,editable=True)   
    status=models.CharField(max_length=10)
    price=models.IntegerField()