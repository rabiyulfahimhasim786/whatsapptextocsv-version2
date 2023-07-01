from django.db import models

class whatsapp(models.Model):
    chat = models.FileField(upload_to='media')

    def __str__(self):
        return self.chat
class CustomizeEmailLeads(models.Model):
    Fileupload = models.FileField(upload_to='media')

    def __str__(self):
        return self.Fileupload
    
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

class Emailsample(models.Model):
    firstname = models.TextField(blank=True)
    lastname = models.TextField(blank=True)
    email = models.TextField(blank=True)
    username = models.TextField(blank=True)
    password = models.TextField(blank=True)
    company = models.TextField(blank=True)
    phonenumber = models.TextField(blank=True)
    address = models.TextField(blank=True)
    address2 = models.TextField(blank=True)
    city = models.TextField(blank=True)
    state = models.TextField(blank=True)
    zipcode = models.TextField(blank=True)
    occupation = models.TextField(blank=True)
    description = models.TextField(blank=True)
    samplecheckstatus = models.PositiveSmallIntegerField(default=1)
    sampledropdownlist = models.TextField(default="New")

    def __str__(self):
        # Implement the logic to calculate and return the refusal time
        # You can access the model's fields and perform calculations or transformations here
        return self.firstname 


# class Film(models.Model):
#     refdate = models.TextField(blank=True)
#     reftitle = models.TextField(blank=True)
#     refyear = models.TextField(blank=True)
#     reffilmurl = models.TextField(blank=True)
    
#     checkstatus = models.PositiveSmallIntegerField(default=1)
#     dropdownlist = models.TextField(default="New")

    
#     def __str__(self):
#         return self.title