from django.db import models

# Create your models here.


class EmailModel(models.Model):
    Subject = models.TextField()
    Sender = models.TextField()
    Received_Time = models.TextField()
    Email_content = models.TextField()
    # Add more fields as necessary

class Totalexperience(models.Model):
    years=models.TextField()
    