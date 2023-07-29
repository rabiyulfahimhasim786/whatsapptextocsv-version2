from django.db import models
# from django.utils.timezone import now
from datetime import datetime

# current dateTime
now = datetime.now()
date = now.strftime("%Y-%m-%d")
class whatsapp(models.Model):
    chat = models.FileField(upload_to='media')

    def __str__(self):
        return self.chat
class CustomizeEmailLeads(models.Model):
    Fileupload = models.FileField(upload_to='media')

    def __str__(self):
        return self.Fileupload
    
class CustomizeBenchsalesLeads(models.Model):
    BenchsalesFile = models.FileField(upload_to='media')

    def __str__(self):
        return self.BenchsalesFile
    
class Film(models.Model):
    date = models.TextField(blank=True)
    title = models.TextField(blank=True)
    year = models.TextField(blank=True)
    filmurl = models.TextField(blank=True)
    checkstatus = models.PositiveSmallIntegerField(default=1)
    dropdownlist = models.TextField(default="New")

    
    def __str__(self):
        return self.title
    
# class Emaillead(models.Model):
#     userdate = models.TextField(blank=True)
#     usertime = models.TextField(blank=True)
#     usermob = models.TextField(blank=True)
#     userdetails = models.TextField(blank=True)
#     emailuserdate = models.TextField(blank=True)
#     emailusertime = models.TextField(blank=True)
#     emailusermob = models.TextField(blank=True)
#     emailuserdetails = models.TextField(blank=True)
#     emailcheckstatus = models.PositiveSmallIntegerField(default=1)
#     emaildropdownlist = models.TextField(default="New")

    
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

    def __str__(self, *args, **kwargs):
        # Implement the logic to calculate and return the refusal time
        # You can access the model's fields and perform calculations or transformations here
        return self.firstname 

# class Customleads(models.Model):
#     leadfirstname = models.TextField(blank=True)
#     leadlastname = models.TextField(blank=True)
#     leademail = models.TextField(blank=True)
#     leadusername = models.TextField(blank=True)
#     leadpassword  = models.TextField(blank=True)
#     leadcompany = models.TextField(blank=True)
#     leadphonenumber = models.TextField(blank=True)
#     leadaddress = models.TextField(blank=True)
#     leadaddress2 = models.TextField(blank=True)
#     leadcity = models.TextField(blank=True)
#     leadstate = models.TextField(blank=True)
#     leadzipcode = models.TextField(blank=True)
#     leadoccupation = models.TextField(blank=True)
#     leaddescription = models.TextField(blank=True)
    

#     def __str__(self, *args, **kwargs):
#         # Implement the logic to calculate and return the refusal time
#         # You can access the model's fields and perform calculations or transformations here
#         return self.leadfirstname
    
# class Custombench(models.Model):
#     benchfirstname = models.TextField(blank=True)
#     benchlastname = models.TextField(blank=True)
#     benchexperience = models.TextField(blank=True)
#     benchcurrentlocation = models.TextField(blank=True)
#     benchtechnology = models.TextField(blank=True)
#     benchrelocation = models.TextField(blank=True)
#     benchvisa = models.TextField(blank=True)
#     benchnoticeperiod = models.TextField(blank=True)
#     benchsalesfirstname = models.TextField(blank=True)
#     benchsaleslastname = models.TextField(blank=True)
#     benchsalescompany = models.TextField(blank=True)
#     benchsalesemail = models.TextField(blank=True)
#     benchsalesmobile = models.TextField(blank=True)
#     benchsalesaddress = models.TextField(blank=True)
    

#     def __str__(self, *args, **kwargs):
#         # Implement the logic to calculate and return the refusal time
#         # You can access the model's fields and perform calculations or transformations here
#         return self.benchfirstname
    
class Customleads(models.Model):
    leadfirstname = models.TextField(blank=True)
    leadlastname = models.TextField(blank=True)
    leademail = models.TextField(blank=True)
    leadusername = models.TextField(blank=True)
    leadpassword  = models.TextField(blank=True)
    leadcompany = models.TextField(blank=True)
    leadphonenumber = models.TextField(blank=True)
    leadaddress = models.TextField(blank=True)
    leadaddress2 = models.TextField(blank=True)
    leadcity = models.TextField(blank=True)
    leadstate = models.TextField(blank=True)
    leadzipcode = models.TextField(blank=True)
    leadposition = models.TextField(blank=True)
    leaddescription = models.TextField(blank=True)
    leadlocation = models.TextField(blank=True)
    leadduration = models.TextField(blank=True)
    leadlegalstatus = models.TextField(blank=True)
    leadinterviewtype = models.TextField(blank=True)
    leadworktype = models.TextField(blank=True)
    leadremote = models.TextField(blank=True)
    leadexperience = models.TextField(blank=True)
    leadrate = models.TextField(blank=True)
    
    

    def __str__(self, *args, **kwargs):
        # Implement the logic to calculate and return the refusal time
        # You can access the model's fields and perform calculations or transformations here
        return self.leadfirstname


  
class Custombench(models.Model):
    benchfirstname = models.TextField(blank=True)
    benchlastname = models.TextField(blank=True)
    benchexperience = models.TextField(blank=True)
    Rate = models.TextField(blank=True)
    Position = models.TextField(blank=True)
    Location = models.TextField(blank=True)
    Duration = models.TextField(blank=True)
    # benchcurrentlocation = models.TextField(blank=True)
    # benchtechnology = models.TextField(blank=True)
    benchrelocation = models.TextField(blank=True)
    Legal_Status = models.TextField(blank=True)
    benchnoticeperiod = models.TextField(blank=True)
    benchsalesfirstname = models.TextField(blank=True)
    benchsaleslastname = models.TextField(blank=True)
    benchsalescompany = models.TextField(blank=True)
    benchsalesemail = models.TextField(blank=True)
    benchsalesmobile = models.TextField(blank=True)
    benchsalesaddress = models.TextField(blank=True)
    Interview_Type = models.TextField(blank=True)
    Work_Type = models.TextField(blank=True)
    Remote = models.TextField(blank=True)
    

    def __str__(self, *args, **kwargs):
        # Implement the logic to calculate and return the refusal time
        # You can access the model's fields and perform calculations or transformations here
        return self.benchfirstname

class Emailbenchsales(models.Model):
    First_Name = models.TextField(blank=True)
    Last_Name = models.TextField(blank=True)
    Experience = models.TextField(blank=True)
    Current_Location = models.TextField(blank=True)
    Technology = models.TextField(blank=True)
    Relocation = models.TextField(blank=True)
    Visa = models.TextField(blank=True)
    Notice_Period = models.TextField(blank=True)
    Benchsales_First_Name = models.TextField(blank=True)
    Benchsales_Last_Name = models.TextField(blank=True)
    Benchsales_Company = models.TextField(blank=True)
    Benchsales_Email = models.TextField(blank=True)
    Benchsales_Mobile = models.TextField(blank=True)
    Benchsales_Address = models.TextField(blank=True)
    bcheckstatus = models.PositiveSmallIntegerField(default=1)
    bdropdownlist = models.TextField(default="Benchsales", blank=True)
    # created_date = models.TextField(default=date, editable=False)
    created_date = models.TextField(default=date, blank=True)

    def __str__(self, *args, **kwargs):
        # Implement the logic to calculate and return the refusal time
        # You can access the model's fields and perform calculations or transformations here
        return self.First_Name 

# class Film(models.Model):
#     refdate = models.TextField(blank=True)
#     reftitle = models.TextField(blank=True)
#     refyear = models.TextField(blank=True)
#     reffilmurl = models.TextField(blank=True)
    
#     checkstatus = models.PositiveSmallIntegerField(default=1)
#     dropdownlist = models.TextField(default="New")

    
#     def __str__(self):
#         return self.title


class Customemailleads(models.Model):
    todaysdate = models.TextField(blank=True)
    Subject = models.TextField(blank=True)
    From = models.TextField(blank=True)
    Received_Time = models.TextField(blank=True)
    Email_Body = models.TextField(blank=True)
    checkstatus = models.PositiveSmallIntegerField(default=1)
    # dropdownlist = models.TextField(default="New")

    
    def __str__(self, *args, **kwargs):
        return self.Subject
    



class Custombenchsales(models.Model):
    bstodaysdate = models.TextField(blank=True)
    bsSubject = models.TextField(blank=True)
    bsFrom = models.TextField(blank=True)
    bsReceived_Time = models.TextField(blank=True)
    bsEmail_Body = models.TextField(blank=True)
    bsEmail_Bodyhtml = models.TextField(blank=True)
    bscheckstatus = models.PositiveSmallIntegerField(default=1)
    # dropdownlist = models.TextField(default="New")

    
    def __str__(self, *args, **kwargs):
        return self.bsSubject