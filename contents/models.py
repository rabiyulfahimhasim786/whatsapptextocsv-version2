from django.db import models

# Create your models here.
class Customwebcontent(models.Model):
    webtodaysdate = models.TextField(blank=True)
    webSubject = models.TextField(blank=True)
    webFrom = models.TextField(blank=True)
    webReceived_Time = models.TextField(blank=True)
    webEmail_Body = models.TextField(blank=True)
    webEmail_Bodyhtml = models.TextField(blank=True)
    webcheckstatus = models.PositiveSmallIntegerField(default=1)
    # dropdownlist = models.TextField(default="New")

    
    def __str__(self, *args, **kwargs):
        return self.webSubject
    
class blogbenchsales(models.Model):
    blogtodaysdate = models.TextField(blank=True)
    blogSubject = models.TextField(blank=True)
    blogFrom = models.TextField(blank=True)
    blogReceived_Time = models.TextField(blank=True)
    blogEmail_Body = models.TextField(blank=True)
    blogEmail_Bodyhtml = models.TextField(blank=True)
    blogcheckstatus = models.PositiveSmallIntegerField(default=1)
    # dropdownlist = models.TextField(default="New")

    
    def __str__(self, *args, **kwargs):
        return self.blogSubject
    