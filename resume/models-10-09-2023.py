from django.db import models


class Resume(models.Model):
    file = models.FileField(upload_to='resumes/')
  
    def __str__(self):
        # return self.file.name
        return str(self.id)


class candidateprofile(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    resumetext = models.TextField( blank=True)
    name = models.CharField(max_length=255,blank=True)
    lastname = models.CharField(max_length=255,blank=True)
    contact_number = models.CharField(max_length=255,blank=True)
    phone_carrier = models.CharField(max_length=255,blank=True)
    email = models.EmailField(max_length=255, blank=True)
    total_experience = models.TextField(blank=True)
    category = models.TextField(blank=True)
    education =models.TextField(blank=True)
    specialization = models.TextField(blank=True)
    legalstatus = models.CharField(max_length=255,blank=True)
    password = models.TextField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=255,blank=True)
    state = models.CharField(max_length=255,blank=True)
    zipcode = models.CharField(max_length=255,blank=True)

    def __str__(self, *args, **kwargs):
        return self.name or str(self.id)

class candidateobjective(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)   
    objectives = models.TextField(blank=True)

    def __str__(self, *args, **kwargs):
        return self.objectives or str(self.id)

class candidateprofessional(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)    
    professional_summary = models.TextField(blank=True)

    def __str__(self, *args, **kwargs):
        return self.professional_summary or str(self.id)
        
class candidateeducation(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)   
    degree = models.TextField(blank=True)
    majordegree = models.TextField(blank=True)
    specializationdegree = models.TextField(blank=True)
    institute = models.TextField(blank=True)
    start_year = models.TextField(blank=True)
    end_year = models.TextField(blank=True)
    institutelocation = models.TextField(blank=True)
    others = models.TextField(blank=True)
    if_others = models.TextField(blank=True)

    def __str__(self, *args, **kwargs):
        return self.degree or str(self.id)

class candidateskill(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)   
    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)

    def __str__(self, *args, **kwargs):
        return self.skills or str(self.id)

class candidateexperience(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)   
    companyname = models.TextField(blank=True)
    job_title = models.TextField(blank=True)
    joblocation = models.TextField(blank=True)
    job_start_year = models.TextField(null=True,blank=True)
    job_end_year = models.TextField(null=True,blank=True)
    job_start_month = models.TextField(null=True,blank=True)
    job_end_month = models.TextField(null=True,blank=True)
    present = models.TextField(null=True,blank=True)
    # present = models.BooleanField(default=False)
    Description = models.TextField(blank=True)
    Responsibilites = models.TextField(blank=True)
    Accomplishments = models.TextField(blank=True)
    skillused = models.TextField(blank=True)

    def __str__(self, args, *kwargs):
        return self.companyname or str(self.id)
    
class candidatereference(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)   
    referred_by = models.TextField(blank=True)
    referrer_email = models.TextField(blank=True)

    def __str__(self, args, *kwargs):
        return self.referred_by or str(self.id) 
    
class candidatecertificate(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)   
    Certification_code = models.TextField(blank=True)
    certification_name = models.TextField(blank=True)
    date_of_certification = models.TextField(blank=True)

    def __str__(self, args, *kwargs):
        return self.Certification_code or str(self.id) 