from django.http import HttpResponse, JsonResponse

import re
from pdfminer.high_level import extract_text
import spacy
from spacy.matcher import Matcher
from .models import Resume, candidateprofile, candidateobjective, candidateprofessional, candidateeducation, candidateskill, candidateexperience, candidatereference, candidatecertificate, candidatereparser, candidateaward, candidatehobbies
from .forms import ResumeUploadForm, candidateprofileForm, candidateobjectiveForm, candidateprofessionalForm, candidateeducationForm, candidateskillForm, candidateexperienceForm, candidatereferenceForm, candidatecertificateForm, candidateawardForm, candidatehobbiesForm
from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render, redirect
import os 
import requests
import json 
from pdfminer.high_level import extract_text
from django.db.models import Count
import spacy
from spacy.matcher import Matcher
from itertools import zip_longest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# dot = './media/'
dot = '/var/www/subdomain/whatsappdata/analysis/media/'
# Helper function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

# Function to extract the candidate's name from a resume
def extract_name(resumetext):
    nlp = spacy.load('en_core_web_sm')
    matcher = Matcher(nlp.vocab)

    # Define name patterns
    patterns = [
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name and Last name
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name, Middle name, and Last name
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]  # First name, Middle name, Middle name, and Last name
        # Add more patterns as needed
    ]

    for pattern in patterns:
        matcher.add('NAME', patterns=[pattern])

    doc = nlp(resumetext)
    matches = matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text

    return None

# Function to extract contact number from a resume text
def extract_contact_number_from_resume(resumetext):
    contact_number = None
    pattern = r"\+?\d{0,2}[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{3,4}"
    match = re.search(pattern, resumetext)

    if match:
        contact_number = match.group()
    else:
        contact_number = ''
    
    return contact_number

# Function to extract email from a resume text
def extract_email_from_resume(resumetext):
    email = None
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    match = re.search(pattern, resumetext)
    
    if match:
        email = match.group()
    else:
        email = ''
    
    return email




def extract_years_from_text(resumetext):
    start_year = []

    # Regular expression pattern to match both date formats (YYYY to YYYY and YYYY – YYYY)
    pattern = r"(\d{4}\s*(?:to|–)\s*\d{4})"

    lines = resumetext.split('\n')
    for line in lines:
        line = line.strip()

        # Check for years information using the pattern
        if re.search(pattern, line):
            years_matches = re.findall(pattern, line)
            for year_range in years_matches:
                start, _ = re.split(r'\s*(?:to|–)\s*', year_range)
                start_year.append(start)


    print(start_year)
    return start_year

def extract_endyears_from_text(resumetext):
    end_year = []

    # Regular expression pattern to match both date formats (YYYY to YYYY and YYYY – YYYY)
    pattern = r"(\d{4}\s*(?:to|–)\s*\d{4})"

    lines = resumetext.split('\n')
    for line in lines:
        line = line.strip()

        # Check for years information using the pattern
        if re.search(pattern, line):
            years_matches = re.findall(pattern, line)
            for year_range in years_matches:
                _, end= re.split(r'\s*(?:to|–)\s*', year_range)
                end_year.append(end)

    print(end_year)
    return end_year



# Function to extract skills from a resume text
def extract_skills_from_resume(resumetext, skills_list):
    skills = []

    for skill in skills_list:
        pattern = r"\b{}\b".format(re.escape(skill))
        match = re.search(pattern, resumetext, re.IGNORECASE)
        
        if match:
            skills.append(skill)
        # else:
        #     skills = ''
        
    return skills

    
def extract_university(resume_text, university_names):
    matching_values = []
    
    # Split the resume text into lines
    lines = resume_text.split('\n')
    
    for line in lines:
        for university in university_names:
            # Create a regex pattern to match the degree name with word boundaries
            pattern = re.compile(r'\b' + re.escape(university) + r'\b', re.IGNORECASE)
            
            # Check if the degree name is found in the line
            if pattern.search(line):
                matching_values.append(line.strip())
                break
    
    if matching_values:
        print("Matching Values:", matching_values)
        universitytuple = tuple(matching_values)
        print(universitytuple)
        return universitytuple
    else:
        print("No matching values found in the resume.")
        return ()

def university_data(resume_text):
  # Sample skill names (replace with actual skill names)
  # skill_names = ["Java", "Python", "SQL", "Data Analysis"]
  university_dataset = requests.get('https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_name_based_names&master_name=school_university')
  dataset = university_dataset.json()
  university_names = [item['name'] for item in dataset['data']]
  universities = ''
  universities = extract_university(resume_text, university_names)


  print(universities)
  return universities



def education_text_below_keywords(resume_text, keywords):
    keyword_pattern = '|'.join(map(re.escape, keywords))
    pattern = rf'({keyword_pattern})\s*([\s\S]*?)(?={keyword_pattern}|\Z)'
    # print(pattern)

    matches = re.findall(pattern, resume_text, re.IGNORECASE)

    extracted_text = {}

    for keyword, text in matches:
        extracted_text[keyword] = text.strip()

    return extracted_text


def education_extraction(resume_text):
  # Keywords to search for
  # keywords_to_extract = ["Education", "Qualification"]
  skills_dataset = requests.get('https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_name_based_names&master_name=education')
  dataset = skills_dataset.json()
  keywords_to_extract = [item['name'] for item in dataset['data']]
  # Extract text below keywords
  extracted_text = education_text_below_keywords(resume_text, keywords_to_extract)

  # Print the extracted text for each keyword
  for keyword, text1 in extracted_text.items():
      text1
      # print(f"Text below '{keyword}':\n{text}\n")\
  if text1 == '':
      text1=''
  return text1




    
def extract_degree_field(degree_text, degree_names):
    matching_values = []
    
    # Split the resume text into lines
    lines = degree_text.split('\n')
    
    
    for line in lines:
        for degree in degree_names:
            # Create a regex pattern to match the degree name with word boundaries
            pattern = re.compile(r'\b' + re.escape(degree) + r'\b', re.IGNORECASE)
            # pattern = re.compile(r'^.*\b' + re.escape(degree) + r'\b.*$', re.IGNORECASE | re.MULTILINE)
            
            # Check if the degree name is found in the line
            if pattern.search(line):
                matching_values.append(line.strip())
                break
    
    if matching_values:
        print("Matching Values:", matching_values)
        educationtuple = tuple(matching_values)
        print(educationtuple)
        return educationtuple
    else:
        print("No matching values found in the resume.")
        return []

def degree_split(document):
    # Sample skill names (replace with actual skill names)
    # skill_names = ["Java", "Python", "SQL", "Data Analysis"]
    degree_dataset = requests.get('https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_name_based_names&master_name=specialization')
    dataset = degree_dataset.json()
    degree_names = [item['name'] for item in dataset['data']]
    # Call the function with the sample resume text and skill names
    degree_data = ''
    degree_data = extract_degree_field(document, degree_names)

    

    print(degree_data)
    return degree_data



def extract_specialization(resume_text, specialization_names):
    matching_values = []

    # Split the resume text into lines
    lines = resume_text.split('\n')

    for line in lines:
        for specialization in specialization_names:
            # Create a regex pattern to match the degree name with word boundaries
            pattern = re.compile(r'\b' + re.escape(specialization) + r'\b', re.IGNORECASE)

            # Check if the degree name is found in the line
            match = pattern.search(line)
            if match:
                # Capture the text following the degree name
                captured_text = line[match.end():].strip()
                captured_text = re.sub(r'<[^>]+>', '', captured_text)
                matching_values.append(captured_text)
                break  # Break out of the inner loop once a match is found

    return matching_values  # Return an empty list if no matches are found

def specialization_split(document):
    try:
        # Sample skill names (replace with actual skill names)
        specialization_dataset = requests.get('https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_name_based_names&master_name=specialization')
        dataset = specialization_dataset.json()
        specialization_names = [item['name'] for item in dataset['data']]

        # Call the function with the sample resume text and skill names
        specialization_data = ''
        specialization_data = extract_specialization(document, specialization_names)
        print(specialization_data)
        
        print(specialization_data)
        return specialization_data
    except Exception as e:
        # Handle exceptions here, such as network errors or JSON parsing errors
        print(f"An error occurred: {str(e)}")
        return ''


def company_info():
    companyurl = 'https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_value_based_values&master_name=benchsales%20recruiter%20company'
    company_dataset = requests.get(companyurl)
    dataset = company_dataset.json()
    company_list = [item['name'] for item in dataset['data']]
    return company_list

def job_info():
    joburl = 'https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_name_based_names&master_name=job%20title'
    job_dataset = requests.get(joburl)
    dataset = job_dataset.json()
    job_list = [item['name'] for item in dataset['data']]
    return job_list
    

def joblocation_info():
    joblocationurl = 'https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_name_based_names&master_name=Job%20Location'
    joblocation_dataset = requests.get(joblocationurl)
    dataset = joblocation_dataset.json()
    joblocation_list = [item['name'] for item in dataset['data']]
    return joblocation_list

def jobdescription_info():
    jobdescriptionurl = 'https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_value_based_values&master_name=Resume%20description'
    jobdescription_dataset = requests.get(jobdescriptionurl)
    dataset = jobdescription_dataset.json()
    jobdescription_list = [item['name'] for item in dataset['data']]
    return jobdescription_list

def jobresponsibilities_info():
    jobresponsibilitiesurl = 'https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_value_based_values&master_name=Resume%20Responsibilities'
    jobresponsibilities_dataset = requests.get(jobresponsibilitiesurl)
    dataset = jobresponsibilities_dataset.json()
    jobresponsibilities_list = [item['name'] for item in dataset['data']]
    return jobresponsibilities_list

def jobaccomplishments_info():
    jobaccomplishmentsurl = 'https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_value_based_values&master_name=Resume%20Accomplishments'
    jobaccomplishments_dataset = requests.get(jobaccomplishmentsurl)
    dataset = jobaccomplishments_dataset.json()
    jobaccomplishments_list = [item['name'] for item in dataset['data']]
    return jobaccomplishments_list

def degree_info():
    degreeurl = 'https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_value_based_values&master_name=Resume%20Degree'
    degree_dataset = requests.get(degreeurl)
    dataset = degree_dataset.json()
    degree_list = [item['name'] for item in dataset['data']]
    return degree_list

def university_info():
    universityurl = 'https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_value_based_values&master_name=Resume%20University'
    university_dataset = requests.get(universityurl)
    dataset = university_dataset.json()
    university_list = [item['name'] for item in dataset['data']]
    return university_list

def time_info():
    timeurl = 'https://career.desss.com/dynamic/careerdesssapi.php?action=get_table_values_based_namevalues&table=aliase_value_based_values&master_name=Resume%20Timeperiod'
    time_dataset = requests.get(timeurl)
    dataset = time_dataset.json()
    time_list = [item['name'] for item in dataset['data']]
    return time_list

def save_company_info(experience_data):

    company_list = company_info()
    company_matches = ''
    company_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(company) for company in company_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    company_matches = company_pattern.findall(experience_data)
    # company_match = ','.join(company_match)
    


    print(company_matches)
    return company_matches

def save_job_info(experience_data):
    job_list = job_info()
    job_matches = ''
    job_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(job) for job in job_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    job_matches = job_pattern.findall(experience_data)
    # job_matches = ','.join(job_matches)

    return job_matches

def save_joblocation_info(experience_data):
    joblocation_list = joblocation_info()
    joblocation_matches = ''
    joblocation_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(joblocation) for joblocation in joblocation_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    joblocation_matches = joblocation_pattern.findall(experience_data)
    # joblocation_matches = ','.join(joblocation_matches)

    return joblocation_matches

def save_jobdescription_info(experience_data):
    jobdescription_list = jobdescription_info()
    jobdescription_matches = ''
    jobdescription_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(jobdescription) for jobdescription in jobdescription_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    jobdescription_matches = jobdescription_pattern.findall(experience_data)
    # job_matches = ','.join(job_matches)

    return jobdescription_matches

def save_jobresponsibilities_info(experience_data):
    jobresponsibilities_list = jobresponsibilities_info()
    jobresponsibilities_matches = ''
    jobresponsibilities_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(jobresponsibilities) for jobresponsibilities in jobresponsibilities_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    jobresponsibilities_matches = jobresponsibilities_pattern.findall(experience_data)
    # job_matches = ','.join(job_matches)

    return jobresponsibilities_matches

def save_jobaccomplishments_info(experience_data):
    jobaccomplishments_list = jobaccomplishments_info()
    jobaccomplishments_matches = ''
    jobaccomplishments_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(jobaccomplishments) for jobaccomplishments in jobaccomplishments_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    jobaccomplishments_matches = jobaccomplishments_pattern.findall(experience_data)
    # job_matches = ','.join(job_matches)

    return jobaccomplishments_matches

def save_degree_info(education_data):

    degree_list = degree_info()
    degree_matches = ''
    degree_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(degreedata) for degreedata in degree_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    degree_matches = degree_pattern.findall(education_data)
    degree_matches = [match.replace("&amp;", "&") for match in degree_matches]
    # company_match = ','.join(company_match)

    print(degree_matches)
    return degree_matches

def save_university_info(education_data):
    university_list = university_info()
    university_matches = ''
    university_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(institutedata) for institutedata in university_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    university_matches = university_pattern.findall(education_data)
  
    print(university_matches)
    return university_matches

def save_time_info(education_data):
    time_list = time_info()
    time_matches = ''
    time_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(time) for time in time_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    time_matches = time_pattern.findall(education_data)
    time_matches = [match.replace("&ndash;", "-") for match in time_matches]
  
    print(time_matches)

    start_years = []
    end_years = []

    pattern = r"(\d{4}\s*(?:to|–)\s*\d{4}|\d{4}\s*-\s*\d{4}|\d{4})"
    for line in time_matches:
        years_matches = re.findall(pattern, line)
        for year_range in years_matches:
            years = re.split(r'\s*(?:to|–|-\s*)\s*', year_range)
            if len(years) == 1:
                # Treat it as a single year with no end year
                start_years.append("")
                end_years.append(years[0])
            else:
                start_years.append(years[0])
                end_years.append(years[1])

    print("Start Years:", start_years)
    print("End Years:", end_years)
    return start_years, end_years

def save_experiencetime_info(education_data):
    time_list = time_info()
    experiencetime_matches = ''
    time_pattern = re.compile(r'(?i)(?:' + '|'.join(re.escape(time) for time in time_list) + r')\s*:\s*(.+?)(?=\s*(?:<|$))', re.IGNORECASE)
    experiencetime_matches = time_pattern.findall(education_data)
    experiencetime_matches = [match.replace("&ndash;", "-") for match in experiencetime_matches]
  
    print(experiencetime_matches)

    experiencestart_years = []
    experiencestart_months = []
    experienceend_years = []
    experienceend_months = []

    for experiencetime_match in experiencetime_matches:
        # Check if the time_match contains a hyphen (range format)
        if '-' in experiencetime_match:
            start_month, end_month = re.findall(r'(\w+)\s*(\d{4})', experiencetime_match)
            experiencestart_years.append(int(start_month[1]))
            experiencestart_months.append(start_month[0])
            experienceend_years.append(int(end_month[1]))
            experienceend_months.append(end_month[0])
        else:
            # Handle the format "December 1997 to June 1996"
            parts = re.findall(r'(\w+)\s*(\d{4})', experiencetime_match)
            if len(parts) == 2:
                experiencestart_years.append(int(parts[0][1]))
                experiencestart_months.append(parts[0][0])
                experienceend_years.append(int(parts[1][1]))
                experienceend_months.append(parts[1][0])

    print("Start Years:", experiencestart_years)
    print("Start Months:", experiencestart_months)
    print("End Years:", experienceend_years)
    print("End Months:", experienceend_months)
    return experiencestart_years, experiencestart_months, experienceend_years, experienceend_months

# Function to extract information from a resume
def extract_resume(resume_path):
    # object_lead=candidatereparser.objects.get(id=id)
    # email_content = object_lead.ExperienceParser
    text = extract_text_from_pdf(resume_path)
    name = extract_name(text)
    contact_number = extract_contact_number_from_resume(text)
    email = extract_email_from_resume(text)
    
    #education  text extractions
    educationtext = education_extraction(text)

    
    universities = university_data(educationtext)
    degree_data = degree_split(educationtext)
    specialization_data = specialization_split(text)
    start_year = extract_years_from_text(educationtext)
    end_year = extract_endyears_from_text(educationtext)
    # company_info_result = save_company_info(email_content)
    # print(company_info_result)  
    
    # Fetch skills from an external API or database
    skills_dataset = requests.get('https://career.desss.com/dynamic/careerdesssapi.php?action=skills')
    dataset = skills_dataset.json()
    skills_list = [item['skill_name'] for item in dataset['data']]
    skills = extract_skills_from_resume(text, skills_list)  # Add this line to extract skills
    # print(skills)
    return text, name, contact_number, email, degree_data, specialization_data, universities, start_year, end_year, skills


def upload_and_extract_resume(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Get the latest uploaded resume
            resume = Resume.objects.latest('id')
            resumesample = os.path.join(dot, str(resume.file))
            print(resumesample)
            
            text, name, contact_number, email, degree_data, specialization_data, universities, start_year, end_year, skills = extract_resume(resumesample)

            # company_matches = save_company_info(email_content)
            # Create a candidate profile associated with the uploaded resume
            candidate_profile = candidateprofile.objects.create(
                resume=resume,
                resumetext=text,
                name=name,
                contact_number=contact_number,
                email=email,
            )
                
            # Create a candidate objective
            candidate_objective = candidateobjective.objects.create(
                resume=resume,
                objectives='',
            )

            candidate_professional = candidateprofessional.objects.create(
                resume=resume,
                professional_summary='',
            )

            candidate_reference = candidatereference.objects.create(
                resume=resume,
                referred_by='',
                referrer_email='',
            )

            candidate_certificate = candidatecertificate.objects.create(
                resume=resume,
                Certification_code='',
                certification_name='',
                date_of_certification='',
            )

            candidate_award = candidateaward.objects.create(
                resume=resume,
                award='',
            )

            candidate_hobbies = candidatehobbies.objects.create(
                resume=resume,
                hobbies='',

            )

            candidate_experience = candidateexperience.objects.create(
                resume=resume,
                companyname='',
                job_title='',
                joblocation='',
                job_start_year='',
                job_end_year='',
                job_start_month='',
                job_end_month='',
                present='',
                Description='',
                Responsibilites='',
                Accomplishments='',
                skillused='',

                # skillused=", ".join(skills),

            )
            

            

            # candidatereparser
            candidate_candidatereparser = candidatereparser.objects.create(
                resume=resume,
                ResumeParser= text,
                ExperienceParser='',
                EducationParser='',
                CertificateParser='',
            )

            for j in range(len(skills)):
                candidate_skill = candidateskill(
                    resume=resume,
                    skills=skills[j],

                )
                candidate_skill.save()
            if int(len(skills))==0:
                candidate_skill = candidateskill.objects.create(
                resume=resume,
                skills='',
                experience='',
                )
 
            start_years_str = ", ".join(start_year)
            end_years_str = ", ".join(end_year)
            # Create a candidateeducation instance for each education record
            for i in range(len(degree_data)):
                education_record = candidateeducation(
                    resume=resume,
                    degree=degree_data[i],
                    majordegree=specialization_data[i],
                    institute=universities[i],
                    start_year=start_years_str.split(", ")[i],
                    end_year=end_years_str.split(", ")[i],
                    specializationdegree ='',
                    institutelocation='',
                    others='',
                    if_others='',
                    # start_year=start_years_str[i],  # Convert list to a comma-separated string
                    # end_year=end_years_str[i], 
                )
                education_record.save()

            if int(len(degree_data))==0:
                education_record = candidateeducation.objects.create(
                resume=resume,
                degree='',
                majordegree='',
                specializationdegree='',
                institute='',
                start_year='',
                end_year='',
                institutelocation='',
                others='',
                if_others='',
                )

            # Remove the uploaded file
            if os.path.exists(resumesample):
                # os.remove(resumesample)
                print('Removed')
                candidates = candidateprofile.objects.all()
                return redirect('extracted_resumes')
            return render(request, 'extracted_resume_list.html', {'form': form, 'candidate_skill': candidate_skill, 'extracted_data': candidate_profile, 'candidate_experience': candidate_experience, 'candidate_certificate': candidate_certificate, 'candidate_objective': candidate_objective, 'candidate_professional':candidate_professional, 'candidate_reference':candidate_reference,  'candidate_education': education_record, 'resume_text': text,'extracted_resumes': candidates, 'candidate_candidatereparser': candidate_candidatereparser, 'candidate_award': candidate_award, 'candidate_hobbies': candidate_hobbies})

    else:
        form = ResumeUploadForm()
        candidates = candidateprofile.objects.all()
    return render(request, 'resume/upload_and_extract_resume.html', {'form': form,'extracted_resumes': candidates})




def success_view(request):
    return render(request, 'resume/success.html')


def extracted_resume_list(request):
    ordering = '-id'  
    details = candidateprofile.objects.filter().order_by(ordering)

    page_number = request.GET.get('page', 1)
       
    
    paginator = Paginator(details, 10) 

    try:
        # Get the current page's details
        details = paginator.page(page_number)
    except EmptyPage:
        # If the requested page is out of range, return the last page
        details = paginator.page(paginator.num_pages)

    num_pages_minus_2 = paginator.num_pages - 2

    context = {
        'details': details,
        'num_pages_minus_2': num_pages_minus_2,
    }

    return render(request, 'resume/extracted_resume_list.html',  context)



def update_profile(request,pk):
    # extracted_resume = get_object_or_404(candidate, pk=pk)
    extracted_profile =candidateprofile.objects.get(id=pk)  
    overall_resumetext = extracted_profile.resumetext

    if request.method == 'POST':
        resumetext = request.POST.get('resumetext', '')
        name = request.POST.get('name', '')
        lastname = request.POST.get('lastname', '')
        contact_number = request.POST.get('contact_number', '')
        phone_carrier = request.POST.get('phone_carrier', '')
        email = request.POST.get('email', '')
        total_experience = request.POST.get('total_experience', '')
        category = request.POST.get('category', '')
        education =request.POST.get('education', '')
        specialization = request.POST.get('specialization', '')
        legalstatus =request.POST.get('legalstatus', '')
        password = request.POST.get('password', '')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zipcode = request.POST.get('zipcode', '')
       
        
        extracted_profile.resumetext = resumetext
        extracted_profile.name = name
        extracted_profile.lastname = lastname
        extracted_profile.contact_number = contact_number
        extracted_profile.phone_carrier = phone_carrier
        extracted_profile.email = email
        extracted_profile.total_experience = total_experience
        extracted_profile.category = category
        extracted_profile.education =education
        extracted_profile.specialization = specialization
        extracted_profile.legalstatus =legalstatus
        extracted_profile.password = password
        extracted_profile.address = address
        extracted_profile.city = city
        extracted_profile.state = state
        extracted_profile.zipcode = zipcode
 

        extracted_profile.save()

        return redirect('edit_extracted_resume', pk=pk)
    return redirect('extracted_resumes')

def update_objective(request,pk):
    # extracted_resume = get_object_or_404(candidate, pk=pk)
    extracted_objective =candidateobjective.objects.get(id=pk)  


    if request.method == 'POST':        
        objectives = request.POST.get('objectives', '')
        
       
        extracted_objective.objectives = objectives
 

        extracted_objective.save()

        return redirect('edit_extracted_resume', pk=pk)
    return redirect('extracted_resumes')

def update_professional(request,pk):
    extracted_professional =candidateprofessional.objects.get(id=pk)  

    if request.method == 'POST':
        professional_summary = request.POST.get('professional_summary', '')
        
        
        extracted_professional.professional_summary = professional_summary

        extracted_professional.save()

        return redirect('edit_extracted_resume', pk=pk)
    return redirect('extracted_resumes')


def update_education(request, pk):
    extracted_resume = get_object_or_404(Resume, id=pk)  # Assuming Resume is the related model
    education_instances = candidateeducation.objects.filter(resume=extracted_resume).order_by('id')

    if request.method == 'POST':
        num_education = candidateeducation.objects.filter(resume=extracted_resume).count()

        # Update skills and experience based on the number provided
        for j in range(1, num_education + 1):
            degree_name = f'leaddegree{j}'
            majordegree_name = f'leadmajor{j}'
            specializationdegree_name = f'leadspecializations{j}'
            institute_name = f'leadinstitute{j}'
            start_year_name = f'leadstart_year{j}'
            end_year_name = f'leadend_year{j}'
            institutelocation_name = f'lead_institutelocation{j}'
            others_name = f'lead_others{j}'
            if_others_name = f'lead_if_others{j}'
            
            degree = request.POST.get(degree_name, '')
            majordegree = request.POST.get(majordegree_name, '')
            specializationdegree = request.POST.get(specializationdegree_name, '')
            institute = request.POST.get(institute_name, '')
            start_year = request.POST.get(start_year_name, '')
            end_year = request.POST.get(end_year_name, '')
            institutelocation = request.POST.get(institutelocation_name, '')
            others = request.POST.get(others_name, '')
            if_others = request.POST.get(if_others_name, '')
            
            # Get the specific skill instance to update
            education_instance = education_instances[j - 1]

            print(education_instances[j - 1])
            education_instance.degree = degree
            education_instance.majordegree = majordegree
            education_instance.specializationdegree = specializationdegree
            education_instance.institute = institute
            education_instance.start_year = start_year
            education_instance.end_year = end_year
            education_instance.institutelocation = institutelocation
            education_instance.others = others
            education_instance.if_others = if_others
            education_instance.save()

        return redirect('edit_extracted_resume', pk=pk)  # Redirect to a success page after update

    return redirect('extracted_resumes')  # Redirect to a success page after update

def update_skill(request, pk):
    extracted_resume = get_object_or_404(Resume, id=pk)  # Assuming Resume is the related model
    skill_instances = candidateskill.objects.filter(resume=extracted_resume).order_by('id')

    if request.method == 'POST':
        num_skills = candidateskill.objects.filter(resume=extracted_resume).count()

        # Update skills and experience based on the number provided
        for i in range(1, num_skills + 1):
            skill_name = f'leadskills{i}'
            experience_name = f'leadexperience{i}'
            
            skills = request.POST.get(skill_name, '')
            experience = request.POST.get(experience_name, '')
            
            # Get the specific skill instance to update
            skill_instance = skill_instances[i - 1]
            # print(skill_instances[i - 1])
            skill_instance.skills = skills
            skill_instance.experience = experience
            skill_instance.save()

        return redirect('edit_extracted_resume', pk=pk)  # Redirect to a success page after update

    return redirect('extracted_resumes')  # Redirect to a success page after update

def update_reference(request, pk):
    extracted_resume = get_object_or_404(Resume, id=pk)  # Assuming Resume is the related model
    reference_instances = candidatereference.objects.filter(resume=extracted_resume).order_by('id')

    if request.method == 'POST':
        num_reference = candidatereference.objects.filter(resume=extracted_resume).count()

        # Update skills and experience based on the number provided
        for k in range(1, num_reference + 1):
            referred_by_name = f'leadreferred{k}'
            referrer_email_name = f'leadreferrer{k}'
            
            referred_by = request.POST.get(referred_by_name, '')
            referrer_email = request.POST.get(referrer_email_name, '')
            
            # Get the specific skill instance to update
            reference_instance = reference_instances[k - 1]
            # print(skill_instances[i - 1])
            reference_instance.referred_by = referred_by
            reference_instance.referrer_email = referrer_email
            reference_instance.save()

        return redirect('edit_extracted_resume', pk=pk)  # Redirect to a success page after update

    return redirect('extracted_resumes')  # Redirect to a success page after update

def update_experience(request, pk):
    extracted_resume = get_object_or_404(Resume, id=pk)  # Assuming Resume is the related model
    experience_instances = candidateexperience.objects.filter(resume=extracted_resume).order_by('id')

    if request.method == 'POST':
        num_experience = candidateexperience.objects.filter(resume=extracted_resume).count()

        # Update skills and experience based on the number provided
        for m in range(1, num_experience + 1):
            companyname_name = f'leaddcompanyname{m}'
            job_title_name = f'leadjob_title{m}'
            skillused_name = f'leadskillused{m}'
            joblocation_name = f'leadjoblocation{m}'
            job_start_year_name = f'leadjob_start_year{m}'
            job_end_year_name = f'leadjob_end_year{m}'
            job_start_month_name = f'leadjob_start_month{m}'
            job_end_month_name = f'leadjob_end_month{m}'
            present_name = f'leadpresent{m}'
            Description_name = f'leadDescription{m}'
            Responsibilites_name = f'leadResponsibilites{m}'
            Accomplishments_name = f'leadAccomplishments{m}'

            companyname = request.POST.get(companyname_name, '')
            job_title = request.POST.get(job_title_name, '')
            skillused = request.POST.get(skillused_name, '')
            joblocation = request.POST.get(joblocation_name, '')
            job_start_year = request.POST.get(job_start_year_name, '')
            job_end_year = request.POST.get(job_end_year_name, '')
            job_start_month = request.POST.get(job_start_month_name, '')
            job_end_month = request.POST.get(job_end_month_name, '')
            present = request.POST.get(present_name, '')
            Description = request.POST.get(Description_name, '')
            Responsibilites = request.POST.get(Responsibilites_name, '')
            Accomplishments = request.POST.get(Accomplishments_name, '')

            
            # Get the specific skill instance to update
            experience_instance = experience_instances[m - 1]
            # print(skill_instances[i - 1])
            experience_instance.companyname = companyname
            experience_instance.job_title = job_title
            experience_instance.skillused = skillused
            experience_instance.joblocation = joblocation or ''
            experience_instance.job_start_year = job_start_year or ''
            experience_instance.job_end_year = job_end_year or ''
            experience_instance.job_start_month = job_start_month or ''
            experience_instance.job_end_month = job_end_month or ''
            experience_instance.present = present or ''
            experience_instance.Description = Description
            experience_instance.Responsibilites = Responsibilites
            experience_instance.Accomplishments = Accomplishments


            experience_instance.save()

        return redirect('edit_extracted_resume', pk=pk)  # Redirect to a success page after update

    return redirect('extracted_resumes')  # Redirect to a success page after update

def update_certificate(request, pk):
    extracted_resume = get_object_or_404(Resume, id=pk)  # Assuming Resume is the related model
    certificate_instances = candidatecertificate.objects.filter(resume=extracted_resume).order_by('id')

    if request.method == 'POST':
        num_reference = candidatecertificate.objects.filter(resume=extracted_resume).count()

        # Update skills and experience based on the number provided
        for L in range(1, num_reference + 1):
            Certification_code_name = f'leadcertificatecode{L}'
            certification_name_name = f'leadcertificatename{L}'
            date_of_certification_name = f'leaddatecertification{L}'
            
            Certification_code = request.POST.get(Certification_code_name, '')
            certification_name = request.POST.get(certification_name_name, '')
            date_of_certification = request.POST.get(date_of_certification_name, '')
            
            # Get the specific skill instance to update
            certificate_instance = certificate_instances[L - 1]
            # print(skill_instances[i - 1])
            certificate_instance.Certification_code = Certification_code
            certificate_instance.certification_name = certification_name
            certificate_instance.date_of_certification = date_of_certification
            certificate_instance.save()

        return redirect('edit_extracted_resume', pk=pk)  # Redirect to a success page after update

    return redirect('extracted_resumes')  # Redirect to a success page after update

def update_award(request, pk):
    extracted_resume = get_object_or_404(Resume, id=pk)  # Assuming Resume is the related model
    award_instances = candidateaward.objects.filter(resume=extracted_resume).order_by('id')

    if request.method == 'POST':
        num_award = candidateaward.objects.filter(resume=extracted_resume).count()

        # Update skills and experience based on the number provided
        for q in range(1, num_award + 1):
            award_name = f'leadaward{q}'
            
            award = request.POST.get(award_name, '')
            
            # Get the specific skill instance to update
            award_instance = award_instances[q - 1]
            award_instance.award = award
            award_instance.save()

        return redirect('edit_extracted_resume', pk=pk) 

    return redirect('extracted_resumes') 

def update_hobbies(request, pk):
    extracted_resume = get_object_or_404(Resume, id=pk)  # Assuming Resume is the related model
    hobbies_instances = candidatehobbies.objects.filter(resume=extracted_resume).order_by('id')

    if request.method == 'POST':
        num_hobbies = candidatehobbies.objects.filter(resume=extracted_resume).count()

        # Update skills and experience based on the number provided
        for v in range(1, num_hobbies + 1):
            hobbies_name = f'leadhobbies{v}'
            
            hobbies = request.POST.get(hobbies_name, '')
            
            # Get the specific skill instance to update
            hobbies_instance = hobbies_instances[v - 1]
            hobbies_instance.hobbies = hobbies
            hobbies_instance.save()

        return redirect('edit_extracted_resume', pk=pk) 

    return redirect('extracted_resumes') 

def edit_optimization(pk):
    try:
        extracted_resume = candidateprofile.objects.get(id=pk)
    except candidateprofile.DoesNotExist:
        extracted_resume = None  # Initialize with None if not found

    try:
        extracted_professional = candidateprofessional.objects.get(id=pk)
    except candidateprofessional.DoesNotExist:
        extracted_professional = None  # Initialize with None if not found

    try:
        extracted_objective = candidateobjective.objects.get(id=pk)
    except candidateobjective.DoesNotExist:
        extracted_objective = None  # Initialize with None if not found

    try:
        extracted_education = candidateeducation.objects.get(id=pk)
    except candidateeducation.DoesNotExist:
        extracted_education = None  # Initialize with None if not found

    try:
        extracted_skill = candidateskill.objects.get(id=pk)
    except candidateskill.DoesNotExist:
        extracted_skill = None  # Initialize with None if not found

    try:
        extracted_experience = candidateexperience.objects.get(id=pk)
    except candidateexperience.DoesNotExist:
        extracted_experience = None  # Initialize with None if not found

    try:
        extracted_reference = candidatereference.objects.get(id=pk)
    except candidatereference.DoesNotExist:
        extracted_reference = None  # Initialize with None if not found
    
    try:
        extracted_certificate = candidatecertificate.objects.get(id=pk)
    except candidatecertificate.DoesNotExist:
        extracted_certificate = None  # Initialize with None if not found

    try:
        extracted_award = candidateaward.objects.get(id=pk)
    except candidateaward.DoesNotExist:
        extracted_award = None  # Initialize with None if not found

    try:
        extracted_hobbies = candidatehobbies.objects.get(id=pk)
    except candidatehobbies.DoesNotExist:
        extracted_hobbies = None  # Initialize with None if not found
    

    return (
        extracted_resume, extracted_education, extracted_skill, extracted_experience,
        extracted_professional, extracted_objective, extracted_reference, extracted_certificate, extracted_award, extracted_hobbies
    )



def edit_extracted_resume(request, pk):
    # Fetch the Resume instance or return a 404 error if it doesn't exist
    resume = get_object_or_404(Resume, id=pk)


    # Fetch associated child models based on the ForeignKey relationship
    profile = candidateprofile.objects.filter(resume=resume).first()
    objective = candidateobjective.objects.filter(resume=resume).first()
    professional = candidateprofessional.objects.filter(resume=resume).first()
    education = candidateeducation.objects.filter(resume=resume).first()
    skill = candidateskill.objects.filter(resume=resume).first()
    if resume == None:
        extracted_profile =candidateprofile.objects.get(id=pk)
        extracted_objective =candidateobjective.objects.get(id=pk)
        extracted_professional =candidateprofessional.objects.get(id=pk)
        reparser_professional =candidatereparser.objects.get(id=pk)
        resumefile =Resume.objects.get(id=pk)
        
    else:
        extracted_profile =candidateprofile.objects.get(id=pk) 
        extracted_objective =candidateobjective.objects.get(id=pk)
        extracted_professional =candidateprofessional.objects.get(id=pk)
        reparser_professional =candidatereparser.objects.get(id=pk)
        resumefile =Resume.objects.get(id=pk)


    skill_data = candidateskill.objects.filter(resume=resume).values('id', 'skills', 'experience')
    education_data = candidateeducation.objects.filter(resume=resume).values('id', 'degree', 'majordegree', 'specializationdegree', 'institute', 'start_year', 'end_year', 'institutelocation', 'others', 'if_others')
    work_data = candidateexperience.objects.filter(resume=resume).values('id', 'companyname', 'job_title', 'skillused', 'joblocation', 'job_start_year', 'job_end_year', 'present', 'Description', 'Responsibilites', 'Accomplishments')
    reference_data = candidatereference.objects.filter(resume=resume).values('id', 'referred_by', 'referrer_email')
    certificate_data = candidatecertificate.objects.filter(resume=resume).values('id', 'Certification_code', 'certification_name', 'date_of_certification')
    award_data = candidateaward.objects.filter(resume=resume).values('id', 'award')
    hobbies_data = candidatehobbies.objects.filter(resume=resume).values('id', 'hobbies')
    # print(skill_data)
    experience = candidateexperience.objects.filter(resume=resume).first()
    reference = candidatereference.objects.filter(resume=resume).first()
    certificate = candidatecertificate.objects.filter(resume=resume).first()
    award = candidateaward.objects.filter(resume=resume).first()
    hobbies = candidatehobbies.objects.filter(resume=resume).first()
    #print(skill)
    overall_resumetext = profile.resumetext if profile else ""



    context = {
        'extracted_resume': resume,
        'profile_form': candidateprofileForm(instance=profile),
        'objective_form': candidateobjectiveForm(instance=objective),
        'professional_form': candidateprofessionalForm(instance=professional),
        'education_form': candidateeducationForm(instance=education),
        'skill_form': candidateskillForm(instance=skill),
        'experience_form': candidateexperienceForm(instance=experience),
        'reference_form': candidatereferenceForm(instance=reference),
        'certificate_form': candidatecertificateForm(instance=certificate),
        'award_form': candidateawardForm(instance=award),
        'hobbies_form': candidatehobbiesForm(instance=hobbies),
        'overall_resumetext': overall_resumetext,
        'skill_data':skill_data,
        'work_data':work_data,
        'reference_data':reference_data,
        'certificate_data':certificate_data,
        'award_data':award_data,
        'hobbies_data':hobbies_data,
        'education_data':education_data,
        'extracted_profile': extracted_profile,
        'extracted_objective':extracted_objective,
        'extracted_professional':extracted_professional,
        'reparser_professional':reparser_professional,
        'resumefile':resumefile,
    }

    if request.method == 'POST':
        # Process the forms individually
        profile_form = candidateprofileForm(request.POST, instance=profile)
        objective_form = candidateobjectiveForm(request.POST, instance=objective)
        professional_form = candidateprofessionalForm(request.POST, instance=professional)
        education_form = candidateeducationForm(request.POST, instance=education)
        skill_form = candidateskillForm(request.POST, instance=skill)
        experience_form = candidateexperienceForm(request.POST, instance=experience)
        reference_form = candidatereferenceForm(request.POST, instance=reference)
        certificate_form = candidatecertificateForm(request.POST, instance=certificate)
        award_form = candidateawardForm(request.POST, instance=award)
        hobbies_form = candidatehobbiesForm(request.POST, instance=hobbies)

        # Check if all forms are valid
        if (
            profile_form.is_valid() and
            objective_form.is_valid() and
            professional_form.is_valid() and
            education_form.is_valid() and
            skill_form.is_valid() and
            reference_form.is_valid() and
            certificate_form.is_valid() and
            award_form.is_valid() and
            hobbies_form.is_valid() and
            experience_form.is_valid()
        ):
            # Save each form individually
            if profile:
                profile_form.save()
            if objective:
                objective_form.save()
            if professional:
                professional_form.save()
            if education:
                education_form.save()
            if skill:
                skill_form.save()
            if experience:
                experience_form.save()
            if reference:
                reference_form.save()
            if certificate:
                certificate_form.save()
            if award:
                award_form.save()
            if hobbies:
                hobbies_form.save()

            # Redirect to a success page or return a success response
            return redirect('extracted_resumes')  # You can replace 'success_page' with the appropriate URL or view name.

    return render(request, 'resume/edit.html', context)





def delete_extracted_resume(request, pk):
    resume = get_object_or_404(Resume, pk=pk)
    
    # Assuming you have ForeignKey relationships between Resume and child models, 
    # you can delete related records through the Resume instance.
    if request.method == 'POST':
        candidateprofile.objects.filter(resume=resume).delete()
        candidateobjective.objects.filter(resume=resume).delete()
        candidateprofessional.objects.filter(resume=resume).delete()
        candidateeducation.objects.filter(resume=resume).delete()
        candidateexperience.objects.filter(resume=resume).delete()
        candidateskill.objects.filter(resume=resume).delete()
        candidatereference.objects.filter(resume=resume).delete()
        candidatecertificate.objects.filter(resume=resume).delete()
        candidateaward.objects.filter(resume=resume).delete()
        candidatehobbies.objects.filter(resume=resume).delete()
        
        # Now, delete the Resume instance
        resume.delete()
        
        return redirect('extracted_resumes')
    
    context = {
        'extracted_resume': resume,
    }
    return render(request, 'resume/delete_resume.html', context)



def add_candidate_experience(request, pk):
    if request.method =='POST':
        resume_id = request.POST.get('resume') or ''
        companyname = request.POST.get('companyname') or ''
        job_title = request.POST.get('job_title') or ''
        skillused = request.POST.get('skillused') or ''
        joblocation = request.POST.get('joblocation') or ''
        job_start_year = request.POST.get('job_start_year') or ''
        job_end_year = request.POST.get('job_end_year') or ''
        job_start_month = request.POST.get('job_start_month') or ''
        job_end_month = request.POST.get('job_end_month') or ''
        present = request.POST.get('present') or ''
        Description = request.POST.get('Description') or ''
        Responsibilites = request.POST.get('Responsibilites') or ''
        Accomplishments = request.POST.get('Accomplishments') or ''
        resume = Resume.objects.get(id=resume_id)
        # create and save candidate skill instance 
        candidateexperience.objects.create(
            resume = resume,
            companyname = companyname,
            job_title = job_title,
            skillused = skillused,
            joblocation = joblocation,
            job_start_year = job_start_year,
            job_end_year = job_end_year,
            job_start_month = job_start_month,
            job_end_month = job_end_month,
            present =present,
            Description = Description,
            Responsibilites = Responsibilites,
            Accomplishments = Accomplishments,
        )
        # return redirect('extracted_resumes')  # Redirect to a success page
        return redirect('edit_extracted_resume', pk=pk)
    elif request.method =='GET':
        candidateexperiencedata = candidateexperience.objects.get(id=pk)
        return render(request, 'resume/edit.html', {'candidateexperience': candidateexperiencedata})
    else:
            candidateexpform = candidateexperienceForm()

    return render(request, 'resume/edit.html', {'candidateexpform': candidateexpform})

def add(request, pk):
    if request.method =='POST':
        resume_id = request.POST.get('resume') or ''
        skills = request.POST.get('skills') or ''
        experience = request.POST.get('experience') or ''
        # print(skills, experience, resume_id)
        resume = Resume.objects.get(id=resume_id)
        # create and save candidate skill instance 
        candidateskill.objects.create(
            resume = resume,
            skills = skills,
            experience = experience,
        )
        # return redirect('extracted_resumes')  # Redirect to a success page
        return redirect('edit_extracted_resume', pk=pk)
    elif request.method =='GET':
        candidateskilldata = candidateskill.objects.get(id=pk)
        return render(request, 'resume/edit.html', {'candidateskill': candidateskilldata})
    else:
            candidateform = candidateskillForm()

    return render(request, 'resume/edit.html', {'candidateform': candidateform})

def add_education(request, pk):
    if request.method =='POST':
        resume_id = request.POST.get('resume') or ''
        degree = request.POST.get('degree') or ''
        majordegree = request.POST.get('majordegree') or ''
        specializationdegree = request.POST.get('specializationdegree') or ''
        institute = request.POST.get('institute') or ''
        start_year = request.POST.get('start_year') or ''
        end_year = request.POST.get('end_year') or ''
        institutelocation = request.POST.get('institutelocation') or ''
        others = request.POST.get('others') or ''
        if_others = request.POST.get('if_others') or ''
        # print(skills, experience, resume_id)
        resume = Resume.objects.get(id=resume_id)
        # create and save candidate skill instance 
        candidateeducation.objects.create(
            resume = resume,
            degree = degree,
            majordegree = majordegree,
            specializationdegree = specializationdegree,
            institute = institute,
            start_year = start_year,
            end_year = end_year,
            institutelocation = institutelocation,
            others = others,
            if_others = if_others,
        )
        # return redirect('extracted_resumes')  # Redirect to a success page
        return redirect('edit_extracted_resume', pk=pk)
    elif request.method =='GET':
        candidateeducationdata = candidateeducation.objects.get(id=pk)
        return render(request, 'resume/edit.html', {'candidateeducation': candidateeducationdata})
    else:
            candidateform = candidateeducationForm()

    return render(request, 'resume/edit.html', {'candidateform': candidateform})

def add_reference(request, pk):
    if request.method =='POST':
        resume_id = request.POST.get('resume') or ''
        referred_by = request.POST.get('referred_by') or ''
        referrer_email = request.POST.get('referrer_email') or ''
        # print(skills, experience, resume_id)
        resume = Resume.objects.get(id=resume_id)
        # create and save candidate skill instance 
        candidatereference.objects.create(
            resume = resume,
            referred_by = referred_by,
            referrer_email = referrer_email,
        )
        # return redirect('extracted_resumes')  # Redirect to a success page
        return redirect('edit_extracted_resume', pk=pk)
    elif request.method =='GET':
        candidatereferencedata = candidatereference.objects.get(id=pk)
        return render(request, 'resume/edit.html', {'candidatereference': candidatereferencedata})
    else:
            candidateform = candidatereferenceForm()

    return render(request, 'resume/edit.html', {'candidateform': candidateform})


def add_certificate(request, pk):
    if request.method =='POST':
        resume_id = request.POST.get('resume') or ''
        Certification_code = request.POST.get('Certification_code') or ''
        certification_name = request.POST.get('certification_name') or ''
        date_of_certification = request.POST.get('date_of_certification') or ''
        # print(Certification_code, certification_name,date_of_certification, resume_id)
        resume = Resume.objects.get(id=resume_id)
        # create and save candidate skill instance 
        candidatecertificate.objects.create(
            resume = resume,
            Certification_code = Certification_code,
            certification_name = certification_name,
            date_of_certification = date_of_certification,
        )
        
        return redirect('edit_extracted_resume', pk=pk)
    elif request.method =='GET':
        candidatecertificatedata = candidatecertificate.objects.get(id=pk)
        return render(request, 'resume/edit.html', {'candidatereference': candidatecertificatedata})
    else:
            candidateform = candidatecertificateForm()

    return render(request, 'resume/edit.html', {'candidateform': candidateform})

def add_award(request, pk):
    if request.method =='POST':
        resume_id = request.POST.get('resume') or ''
        award = request.POST.get('award') or ''
        resume = Resume.objects.get(id=resume_id)
        # create and save candidate skill instance 
        candidateaward.objects.create(
            resume = resume,
            award = award,
        )
        
        return redirect('edit_extracted_resume', pk=pk)
    elif request.method =='GET':
        candidateawarddata = candidateaward.objects.get(id=pk)
        return render(request, 'resume/edit.html', {'candidateaward': candidateawarddata})
    else:
            candidateform = candidateawardForm()

    return render(request, 'resume/edit.html', {'candidateform': candidateform})

def add_hobbies(request, pk):
    if request.method =='POST':
        resume_id = request.POST.get('resume') or ''
        hobbies = request.POST.get('hobbies') or ''
        resume = Resume.objects.get(id=resume_id)
        # create and save candidate skill instance 
        candidatehobbies.objects.create(
            resume = resume,
            hobbies = hobbies,
        )
        
        return redirect('edit_extracted_resume', pk=pk)
    elif request.method =='GET':
        candidatehobbiesdata = candidatehobbies.objects.get(id=pk)
        return render(request, 'resume/edit.html', {'candidatehobbies': candidatehobbiesdata})
    else:
            candidateform = candidatehobbiesForm()

    return render(request, 'resume/edit.html', {'candidateform': candidateform})


def delete_skills_resume(request, pk):
    resume = get_object_or_404(Resume, id=pk)

    if request.method == 'POST':
        delete_idd = request.POST.get('id')

        # Check if 'id' is provided and a valid integer
        if delete_idd:
            try:
                id = int(delete_idd)
                candidate_profile = candidateskill.objects.filter(id=id,resume_id=resume)
                candidate_profile.delete()
                return redirect('edit_extracted_resume', pk=pk)
            except (ValueError, candidateskill.DoesNotExist):
                return redirect('edit_extracted_resume', pk=pk)

    return redirect('extracted_resumes')

def delete_education_resume(request, pk):
    resume = get_object_or_404(Resume, id=pk)

    if request.method == 'POST':
        delete_idd = request.POST.get('id')
        if delete_idd:
            try:
                id = int(delete_idd)
                candidate_profile = candidateeducation.objects.filter(id=id,resume_id=resume)
                candidate_profile.delete()
                return redirect('edit_extracted_resume', pk=pk)
            except (ValueError, candidateeducation.DoesNotExist):
                return redirect('edit_extracted_resume', pk=pk)

    return redirect('extracted_resumes')

def delete_experience_resume(request, pk):
    resume = get_object_or_404(Resume, id=pk)

    if request.method == 'POST':
        delete_idd = request.POST.get('id')

        # Check if 'id' is provided and a valid integer
        if delete_idd:
            try:
                id = int(delete_idd)
                candidate_profile = candidateexperience.objects.filter(id=id,resume_id=resume)
                candidate_profile.delete()
                return redirect('edit_extracted_resume', pk=pk)
            except (ValueError, candidateexperience.DoesNotExist):
                return redirect('edit_extracted_resume', pk=pk)

    return redirect('extracted_resumes')

def delete_reference_resume(request, pk):
    resume = get_object_or_404(Resume, id=pk)

    if request.method == 'POST':
        delete_idd = request.POST.get('id')

        # Check if 'id' is provided and a valid integer
        if delete_idd:
            try:
                id = int(delete_idd)
                candidate_profile = candidatereference.objects.filter(id=id,resume_id=resume)
                candidate_profile.delete()
                return redirect('edit_extracted_resume', pk=pk)
            except (ValueError, candidatereference.DoesNotExist):
                return redirect('edit_extracted_resume', pk=pk)

    return redirect('extracted_resumes')

def delete_certificate_resume(request, pk):
    resume = get_object_or_404(Resume, id=pk)

    if request.method == 'POST':
        delete_idd = request.POST.get('id')

        # Check if 'id' is provided and a valid integer
        if delete_idd:
            try:
                id = int(delete_idd)
                candidate_profile = candidatecertificate.objects.filter(id=id,resume_id=resume)
                candidate_profile.delete()
                return redirect('edit_extracted_resume', pk=pk)
            except (ValueError, candidatecertificate.DoesNotExist):
                return redirect('edit_extracted_resume', pk=pk)

    return redirect('extracted_resumes')

def delete_award_resume(request, pk):
    resume = get_object_or_404(Resume, id=pk)

    if request.method == 'POST':
        delete_idd = request.POST.get('id')

        # Check if 'id' is provided and a valid integer
        if delete_idd:
            try:
                id = int(delete_idd)
                candidate_profile = candidateaward.objects.filter(id=id,resume_id=resume)
                candidate_profile.delete()
                return redirect('edit_extracted_resume', pk=pk)
            except (ValueError, candidateaward.DoesNotExist):
                return redirect('edit_extracted_resume', pk=pk)

    return redirect('extracted_resumes')

def delete_hobbies_resume(request, pk):
    resume = get_object_or_404(Resume, id=pk)

    if request.method == 'POST':
        delete_idd = request.POST.get('id')

        # Check if 'id' is provided and a valid integer
        if delete_idd:
            try:
                id = int(delete_idd)
                candidate_profile = candidatehobbies.objects.filter(id=id,resume_id=resume)
                candidate_profile.delete()
                return redirect('edit_extracted_resume', pk=pk)
            except (ValueError, candidatehobbies.DoesNotExist):
                return redirect('edit_extracted_resume', pk=pk)

    return redirect('extracted_resumes')

def edit_candidateskill(request, pk):
    candidateskill_instance = get_object_or_404(candidateskill, pk=pk,)
    print(candidateskill_instance)
  
    
    if request.method == 'POST':
        resume = request.POST.get('resume')
        candidateskill_instances = candidateskill.objects.get(id=pk)
        skills = request.POST.get('skills')
        experience = request.POST.get('experience')
        
        candidateskill_instances.skills = skills
        candidateskill_instances.experience = experience
        candidateskill_instances.save()

        return redirect('edit_extracted_resume', pk=resume)  # Redirect to resume edit view or another appropriate view

    return render(request, 'resume/editskills.html', {'candidateskill_instance': candidateskill_instance})



def get_edit_screen_certificate(request):
    
    if request.method == 'GET':
        master_id = request.GET.get('master_id')
        certificate_id = request.GET.get('certificate_id')
        candidate_profile = candidatecertificate.objects.get(id=certificate_id)
        Certification_code = candidate_profile.Certification_code
        certification_name = candidate_profile.certification_name
        date_of_certification = candidate_profile.date_of_certification

        
        return JsonResponse({"Certification_code":Certification_code, "certification_name":certification_name, "date_of_certification":date_of_certification})



def edit_certificate_code(request, pk):
    if request.method == 'POST':
        master_id = request.POST.get('master_id')
        certificate_id = request.POST.get('code_name_id')
        Certification_code = request.POST.get('Certification_code')
        certification_name = request.POST.get('certification_name')
        date_of_certification = request.POST.get('date_of_certification')

        print(master_id) 
        print(certificate_id)
        print(Certification_code)
        print(certification_name)
        print(date_of_certification)

        candidate_certificate, created = candidatecertificate.objects.get_or_create(id=certificate_id, resume_id=master_id)
        candidate_certificate.Certification_code = Certification_code
        candidate_certificate.certification_name = certification_name
        candidate_certificate.date_of_certification = date_of_certification
        candidate_certificate.save()
        

    return redirect('edit_extracted_resume', pk=pk)

def get_edit_screen_award(request):
    
    if request.method == 'GET':
        master_id = request.GET.get('master_id')
        award_id = request.GET.get('award_id')
        candidate_profile = candidateaward.objects.get(id=award_id)
        award = candidate_profile.award
        
        return JsonResponse({"award":award})



def edit_award(request, pk):
    if request.method == 'POST':
        master_id = request.POST.get('master_id')
        award_id = request.POST.get('award_name_id')
        award = request.POST.get('award')

        print(master_id) 
        print(award_id)
        print(award)

        candidate_award, created = candidateaward.objects.get_or_create(id=award_id, resume_id=master_id)
        candidate_award.award = award
        candidate_award.save()
        
    return redirect('edit_extracted_resume', pk=pk)

def get_edit_screen_hobbies(request):
    
    if request.method == 'GET':
        master_id = request.GET.get('master_id')
        hobbies_id = request.GET.get('hobbies_id')
        candidate_profile = candidatehobbies.objects.get(id=hobbies_id)
        hobbies = candidate_profile.hobbies
        
        return JsonResponse({"hobbies":hobbies})



def edit_hobbies(request, pk):
    if request.method == 'POST':
        master_id = request.POST.get('master_id')
        hobbies_id = request.POST.get('hobbies_name_id')
        hobbies = request.POST.get('hobbies')

        print(master_id) 
        print(hobbies_id)
        print(hobbies)

        candidate_hobbies, created = candidatehobbies.objects.get_or_create(id=hobbies_id, resume_id=master_id)
        candidate_hobbies.hobbies = hobbies
        candidate_hobbies.save()
        
    return redirect('edit_extracted_resume', pk=pk)

def get_edit_screen_skills_experience(request):
    
    if request.method == 'GET':
        master_id = request.GET.get('master_id')
        skill_id = request.GET.get('skill_id')
        candidate_profile = candidateskill.objects.get(id=skill_id)
        skills = candidate_profile.skills
        experience = candidate_profile.experience

        
        return JsonResponse({"skills":skills, "experience":experience})


def edit_skills_experience(request, pk):
    if request.method == 'POST':
        master_id = request.POST.get('master_id')
        skill_id = request.POST.get('skills_experience_id')
        skills = request.POST.get('skills')
        experience = request.POST.get('experience')

        print(master_id) 
        print(skill_id)
        print(skills)
        print(experience)

        candidate_skill, created = candidateskill.objects.get_or_create(id=skill_id, resume_id=master_id)
        candidate_skill.skills = skills
        candidate_skill.experience = experience
        candidate_skill.save()
        

    return redirect('edit_extracted_resume', pk=pk)




def get_edit_screen_education(request):
    
    if request.method == 'GET':
        master_id = request.GET.get('master_id')
        education_id = request.GET.get('education_id')
        candidate_file = get_object_or_404(candidateeducation, id=int(education_id))
        degree = candidate_file.degree
        majordegree = candidate_file.majordegree
        specializationdegree = candidate_file.specializationdegree
        institute = candidate_file.institute
        start_year = candidate_file.start_year
        end_year = candidate_file.end_year
        institutelocation = candidate_file.institutelocation
        others = candidate_file.others
        if_others = candidate_file.if_others

        
        return JsonResponse({"degree":degree, "majordegree":majordegree, "specializationdegree":specializationdegree, "institute":institute, "start_year":start_year, "end_year":end_year, "institutelocation":institutelocation, "others":others,"if_others":if_others})
    

def edit_education(request, pk):
    if request.method == 'POST':
        master_id = request.POST.get('master_id')
        education_id = request.POST.get('education_degree_id')
        degree = request.POST.get('degree')
        majordegree = request.POST.get('majordegree')
        specializationdegree = request.POST.get('specializationdegree')
        institute = request.POST.get('institute')
        start_year = request.POST.get('start_year')
        end_year = request.POST.get('end_year')
        institutelocation = request.POST.get('institutelocation')
        others = request.POST.get('others')
        if_others = request.POST.get('if_others')

        print(master_id) 
        print(education_id)
        print(degree)
        print(majordegree)
        print(specializationdegree)
        print(institute)
        print(start_year)
        print(end_year)
        print(institutelocation)
        print(others)
        print(if_others)
        

        candidate_education, created = candidateeducation.objects.get_or_create(id= int(education_id), resume_id=int(master_id))
        candidate_education.degree = degree
        candidate_education.majordegree = majordegree
        candidate_education.specializationdegree = specializationdegree
        candidate_education.institute = institute
        candidate_education.start_year = start_year
        candidate_education.end_year = end_year
        candidate_education.institutelocation = institutelocation
        candidate_education.others = others
        candidate_education.if_others = if_others
        candidate_education.save()

    return redirect('edit_extracted_resume', pk=pk)


def get_edit_screen__by_email(request):
    
    if request.method == 'GET':
        master_id = request.GET.get('master_id')
        refer_id = request.GET.get('refer_id')
        candidate_pro_file = candidatereference.objects.get(id=refer_id)
        referred_by = candidate_pro_file.referred_by
        referrer_email = candidate_pro_file.referrer_email

        
        return JsonResponse({"referred_by":referred_by, "referrer_email":referrer_email})


def edit_by_email(request, pk):
    if request.method == 'POST':
        master_id = request.POST.get('master_id')
        refer_id = request.POST.get('referby_email_id')
        referred_by = request.POST.get('referred_by')
        referrer_email = request.POST.get('referrer_email')

        print(master_id) 
        print(refer_id)
        print(referred_by)
        print(referrer_email)

        candidate_reference, created = candidatereference.objects.get_or_create(id=refer_id, resume_id=master_id)
        candidate_reference.referred_by = referred_by
        candidate_reference.referrer_email = referrer_email
        candidate_reference.save()
        

    return redirect('edit_extracted_resume', pk=pk)




def get_edit_screen_experience(request):
    
    if request.method == 'GET':
        master_id = request.GET.get('expmaster_id')
        experience_id = request.GET.get('experience_id')
        print(master_id) 
        print(experience_id)
        candidate_profile1 = candidateexperience.objects.get(id=experience_id)
        companyname = candidate_profile1.companyname
        job_title = candidate_profile1.job_title
        joblocation = candidate_profile1.joblocation
        job_start_year = candidate_profile1.job_start_year
        job_end_year = candidate_profile1.job_end_year
        job_start_month = candidate_profile1.job_start_month
        job_end_month = candidate_profile1.job_end_month
        present = candidate_profile1.present
        Description = candidate_profile1.Description
        Responsibilites = candidate_profile1.Responsibilites
        Accomplishments = candidate_profile1.Accomplishments
        skillused = candidate_profile1.skillused

        
        return JsonResponse({"companyname":companyname, "job_title":job_title, "joblocation":joblocation, "job_start_year":job_start_year,"job_end_year":job_end_year,"job_start_month":job_start_month,"job_end_month":job_end_month,"present":present,"Description":Description,"Responsibilites":Responsibilites,"Accomplishments":Accomplishments,"skillused":skillused})


def edit_experience(request, pk):
    if request.method == 'POST':
        master_id = request.POST.get('master_id')
        experience_id = request.POST.get('res_des_id')
        companyname = request.POST.get('companyname')
        job_title = request.POST.get('job_title')
        joblocation = request.POST.get('joblocation')
        job_start_year = request.POST.get('job_start_year', '')
        job_end_year = request.POST.get('job_end_year', '')
        job_start_month = request.POST.get('job_start_month')
        job_end_month = request.POST.get('job_end_month')
        present = request.POST.get('present')
        Description = request.POST.get('Description')
        Responsibilites = request.POST.get('Responsibilites')
        Accomplishments = request.POST.get('Accomplishments')
        skillused = request.POST.get('skillused')




        # Get the candidateskill instance or create a new one
        candidate_experience, created = candidateexperience.objects.get_or_create(id=experience_id, resume_id=master_id)
        # candidate_experience = candidateexperience.objects.get(id=experience_id)
        candidate_experience.companyname = companyname
        candidate_experience.job_title = job_title
        candidate_experience.joblocation = joblocation
        candidate_experience.job_start_year = job_start_year
        candidate_experience.job_end_year = job_end_year
        candidate_experience.job_start_month = job_start_month
        candidate_experience.job_end_month = job_end_month
        candidate_experience.present = present
        candidate_experience.Description = Description
        candidate_experience.Responsibilites = Responsibilites
        candidate_experience.Accomplishments = Accomplishments
        candidate_experience.skillused = skillused
        candidate_experience.save()
        

    return redirect('edit_extracted_resume', pk=pk)



def get_edit_screen_job_skills(request):
    
    if request.method == 'GET':
        
        master_id = request.GET.get('master_id')
        jobskill_id = request.GET.get('jobskill_id')
        candidate_profile = candidateexperience.objects.get(id=jobskill_id)
        skillused = candidate_profile.skillused
        extracted_resume_skill = get_object_or_404(candidateexperience, pk=jobskill_id)
        # skills_list = extracted_resume.skills.split(",")
        # print(skills_list)
        skills_list = extracted_resume_skill.skillused.split(",")
        if skills_list == ['']:
            zeros_list = [''] * 10
            skills_list =zeros_list
        # print(skills_list)
        output = {}

        for i in range(1, 11):
            key = f"skills{i}"
            if i <= len(skills_list):
                value = skills_list[i - 1]
            else:
                value = ''
            output[key] = value
        # print(output)
        # return JsonResponse({"skills":skillused,'skillslist':skills_list})
        return JsonResponse(output)

def edit_skills_used(request, pk):
    if request.method == 'POST':
        master_id = request.POST.get('master_id')
        skill_id = request.POST.get('job_skills_id')
        skillused = request.POST.get('skillused')
        extracted_resume_skill = get_object_or_404(candidateexperience, pk=skill_id)
        # skills_list = extracted_resume.skills.split(",")
        # print(skills_list)
        skills_list = extracted_resume_skill.skillused.split(",")
        if skills_list == ['']:
            zeros_list = [''] * 10
            skills_list =zeros_list
        print(master_id) 
        print(skill_id)
        print(skillused)
        num_skills = int(len(skills_list))
        skills_data = [] 
        for i in range(1, num_skills + 1):
            skill_name = f'skillused{i}'
                    
                    
            skills = request.POST.get(skill_name, '')
            skills_data .append(skills)

        skillsdatas = ','.join(skills_data)

        candidate_skill, created = candidateexperience.objects.get_or_create(id=skill_id, resume_id=master_id)
        candidate_skill.skillused = skillsdatas
        candidate_skill.save()
        

    return redirect('edit_extracted_resume', pk=pk)


def edit_by_candidatereparser(request, pk):
    if request.method == 'POST':
        resume = request.POST.get('resume')
        resume_data = request.POST.get('resume_data')
        experience_data = request.POST.get('experience_data')
        education_data = request.POST.get('education_data')
        certificate_data = request.POST.get('certificate_data')
        # print(experience_data)
        company_matches = save_company_info(experience_data)
        job_matches = save_job_info(experience_data)
        joblocation_matches = save_joblocation_info(experience_data)
        jobdescription_matches = save_jobdescription_info(experience_data)
        jobresponsibilities_matches = save_jobresponsibilities_info(experience_data)
        jobaccomplishments_matches = save_jobaccomplishments_info(experience_data)
        experiencestart_years, experiencestart_months, experienceend_years, experienceend_months = save_experiencetime_info(experience_data)
        degree_matches = save_degree_info(education_data)
        university_matches = save_university_info(education_data)
        specialization_data = specialization_split(education_data)
        start_years, end_years = save_time_info(education_data)
        candidate_reference, created = candidatereparser.objects.get_or_create(id=pk, resume_id=resume)
        candidate_reference.ResumeParser = resume_data
        candidate_reference.ExperienceParser = experience_data
        candidate_reference.EducationParser = education_data
        candidate_reference.CertificateParser = certificate_data
        candidate_reference.save()   


        # Iterate through the lists and create or update objects for each set of data
        # for company, job, location in zip(company_matches, job_matches, joblocation_matches):
        #     print(company, job, location)
        #     candidate_experience, created = candidateexperience.objects.get_or_create(
        #         resume_id=resume,
        #         companyname=company,
        #         job_title=job,
        #         joblocation=location
        #     )

        #     if not created:
        #         # If the object was created, update its fields
        #         candidate_experience.resume_id = resume
        #         candidate_experience.save()
        #         # print('Updated')
        #     else:
        #         ''

        # Determine the longest list among the three
        max_length = max(len(company_matches), len(job_matches), len(joblocation_matches), len(jobdescription_matches), len(jobresponsibilities_matches), len(jobaccomplishments_matches), len(experiencestart_years), len(experiencestart_months), len(experienceend_years), len(experienceend_months))

        for i in range(max_length):
            company = company_matches[i] if i < len(company_matches) else None
            job = job_matches[i] if i < len(job_matches) else ''
            location = joblocation_matches[i] if i < len(joblocation_matches) else ''
            desc = jobdescription_matches[i] if i < len(jobdescription_matches) else ''
            res = jobresponsibilities_matches[i] if i < len(jobresponsibilities_matches) else ''
            acc = jobaccomplishments_matches[i] if i < len(jobaccomplishments_matches) else ''
            expstart_year = experiencestart_years[i] if i < len(experiencestart_years) else ''
            expstart_month = experiencestart_months[i] if i < len(experiencestart_months) else ''
            expend_year = experienceend_years[i] if i < len(experienceend_years) else ''
            expend_month = experienceend_months[i] if i < len(experienceend_months) else ''

            candidate_experience, created = candidateexperience.objects.get_or_create(
                resume_id=resume,
                companyname=company,
                job_title=job,
                joblocation=location,
                Description=desc,
                Responsibilites=res,
                Accomplishments=acc,
                job_start_year=expstart_year,
                job_end_year=expend_year,
                job_start_month=expstart_month,
                job_end_month=expend_month
            )
            if not created:
                # If the object was created, update its fields
                candidate_experience.resume_id = resume
                candidate_experience.save()
                # print('Updated')
            else:
                ''
        #below code for education 
        max_length_education = max(len(degree_matches), len(university_matches), len(specialization_data), len(start_years), len(end_years))

        for j in range(max_length_education):
            degreedata = degree_matches[j] if j < len(degree_matches) else None
            institutedata = university_matches[j] if j < len(university_matches) else ''
            specialization_matches = specialization_data[j] if j < len(specialization_data) else ''
            restart_years = start_years[j] if j < len(start_years) else ''
            reend_years = end_years[j] if j < len(end_years) else ''

            # print(f"Degree: {degreedata}, Institute: {institutedata}, Specialization: {specialization_matches}")

            candidate_education, created = candidateeducation.objects.get_or_create(
                resume_id=resume,
                degree=degreedata,
                institute=institutedata,
                majordegree=specialization_matches,
                start_year=restart_years,
                end_year=reend_years
            )
            if not created:
                # If the object was created, update its fields
                candidate_education.resume_id = resume
                candidate_education.save()
                # print('Updated')
            else:
                print('Not created')

    return redirect('edit_extracted_resume', pk=pk)