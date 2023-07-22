from django.db import models

class whatsapp(models.Model):
    chat = models.FileField(upload_to='media')

    def __str__(self):
        return self.chat

class Film(models.Model):
    date = models.TextField(blank=True)
    title = models.TextField(blank=True)
    year = models.TextField(blank=True)
    filmurl = models.TextField(blank=True)
    checkstatus = models.PositiveSmallIntegerField(default=1)
    dropdownlist = models.TextField(default="New")

    
    def __str__(self):
        return self.title
    
class Emaillead(models.Model):
    userdate = models.TextField(blank=True)
    usertime = models.TextField(blank=True)
    usermob = models.TextField(blank=True)
    userdetails = models.TextField(blank=True)
    emailuserdate = models.TextField(blank=True)
    emailusertime = models.TextField(blank=True)
    emailusermob = models.TextField(blank=True)
    emailuserdetails = models.TextField(blank=True)
    emailcheckstatus = models.PositiveSmallIntegerField(default=1)
    emaildropdownlist = models.TextField(default="New")

    
    # def __str__(self):
    #     return self.usertime
    


class Emailleadoppurtunities(models.Model):
    refuserdate = models.TextField(blank=True)
    refusertime = models.TextField(blank=True)
    refusermob = models.TextField(blank=True)
    refuserdetails = models.TextField(blank=True)
    refemailuserdate = models.TextField(blank=True)
    refemailusertime = models.TextField(blank=True)
    refemailusermob = models.TextField(blank=True)
    refemailuserdetails = models.TextField(blank=True)
    refcheckstatus = models.PositiveSmallIntegerField(default=1)
    refdropdownlist = models.TextField(default="New")

    
    # def __str__(self):
    #     return self.refusertime
    
# class Film(models.Model):
#     refdate = models.TextField(blank=True)
#     reftitle = models.TextField(blank=True)
#     refyear = models.TextField(blank=True)
#     reffilmurl = models.TextField(blank=True)
    
#     checkstatus = models.PositiveSmallIntegerField(default=1)
#     dropdownlist = models.TextField(default="New")

    
#     def __str__(self):
#         return self.title