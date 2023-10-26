from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage
import regex
import pandas as pd
import numpy as np
import emoji
import csv
import unicodedata
# file formatting important
from datetime import datetime as dt
import json
from collections import Counter
from django.shortcuts import get_object_or_404
import matplotlib.pyplot as plt
#from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from .models import whatsapp, Film, Emailbenchsales, Emailleadoppurtunities, Customleads, Emailsample, CustomizeEmailLeads, CustomizeBenchsalesLeads, Customemailleads, Custombenchsales, Custombench
from .forms import WhatsappForm, FilmForm, LocationChoiceField, LabelChoiceField, DateChoiceField, CustomleadsForm, UploadFileForm, EmailbenchsalesForm, EmailleadoppurtunitiesForm, EmailsampleForm, CustomizeEmailLeadsForm, CustomizeBenchsalesLeadsForm, CustomemailleadsForm, CustombenchsalesForm, CustombenchForm
from rest_framework.response import Response
from django.contrib import messages
import os
import re
import csv
import smtplib
import imaplib
import email
from django.db.models import Q
from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from bs4 import BeautifulSoup
from django.utils.html import strip_tags
import re
import spacy
import csv
import urllib.parse
nlp = spacy.load('en_core_web_sm')

def date_time(s):
    pattern = '^([0-9]+)(\/)([0-9]+)(\/)([0-9]+), ([0-9]+):([0-9]+)[ ]?(AM|PM|am|pm)? -'
    result = regex.match(pattern, s)
    if result:
        return True
    return False

def find_author(s):
    s = s.split(":")
    if len(s)==2:
        return True
    else:
        return False

def getDatapoint(line):
    splitline = line.split(' - ')
    dateTime = splitline[0]
    date, time = dateTime.split(", ")
    message = " ".join(splitline[1:])
    if find_author(message):
        splitmessage = message.split(": ")
        author = splitmessage[0]
        message = " ".join(splitmessage[1:])
    else:
        author= None
    return date, time, author, message

from django.core.cache import cache
from django.apps import apps

def cacheclearance():
    cache.clear()
    return 'ok'
def clear_models_cache():
    # Get all the registered models
    all_models = apps.get_models()
    
    # Iterate over each model and clear cache
    for model in all_models:
        cache_key = f'{model._meta.app_label}.{model._meta.model_name}_cache'
        cache.delete(cache_key)
    return 'ok'


def remove_br_tags_and_spaces(text):
    # Use regular expression to find and remove <br> tags and spaces around them
    cleaned_text = re.sub(r'\s*<br\s*/?>\s*', '\n', text)
    # Remove consecutive line breaks and extra spaces
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text)
    cleaned_text = re.sub(r'\n\s+', '\n', cleaned_text)
    return cleaned_text

def linebreaksbr_fixed(value):
    """
    Replace multiple newline characters with a single <br> tag.
    """
    return re.sub(r'\n+', '<br>', value)

# Assuming you already have the required libraries imported
# Make sure emailfileleads contains the file path to your input CSV file
# emailfileleads = 'path_to_your_input_csv_file.csv'

def process_email_content(content):
    # Process the email text with spaCy for NER
    #nlp = spacy.load('en_core_web_sm')
    doc = nlp(content)

    # Initialize variables to store the extracted "From" address and the last email data
    from_address = ""
    last_email_data = ""

    # Extract "From" address and the last email data
    for sent in doc.sents:
        if "From:" in sent.text:
            from_address = sent.text.replace("From:", "").strip()
        last_email_data = sent.text.strip()

    return from_address, last_email_data

def extract_named_entities(content):
    # Define compiled regex patterns for faster matching
    name_pattern = re.compile(r'From:\s+(.*?)\s+(.*?)\n')
    #position_pattern = re.compile(r'\s+(.*?)\s+(.*?)\n\s*(?:[Aa]t|AT|@)\s.*')
    # phone_pattern =  re.compile(r'\b(?:\+?\d{1,4}[- ]?)?\d{1,}[- ]?\d{1,}[- ]?\d{1,}[- ]?\d{1,}[- ]?\d{1,}\b')
    phone_pattern = re.compile(r'\b\d{3}-\d{3}-\d{4}\b|\b\d{10}\b')
    email_pattern = re.compile(r'[\w\.-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}')
    address_pattern = re.compile(r'[A-Za-z]+(?:,[A-Za-z]+)*(?:\s*,\s*\d{5})?\s*,\s*[A-Za-z]+\s*,\s*[A-Za-z]+\s*,\s*\d{5}\b')
    thanks_pattern = re.compile(r'(?:Thanks\s*&(?:amp;)?\s*regards|Thanks\s*and\s*Regards),\s*(.*?)\s+([A-Za-z]+)')

    # Find the matches using the compiled regex patterns
    name_match = name_pattern.search(content)
    #position_match = position_pattern.search(content)
    phone_matches = phone_pattern.findall(content)
    email_match = email_pattern.search(content)
    address_match = address_pattern.search(content)
    thanks_match = thanks_pattern.search(content)

    # Extract the relevant details from the matches if a match is found
    first_name = name_match.group(1) if name_match else ""
    last_name = name_match.group(2) if name_match else ""
    #position = position_match.group(1) if position_match else ""
    phone = next((num for num in phone_matches if len(num) == 10), "")
    emaildata = email_match.group() if email_match else ""
    address = address_match.group() if address_match else ""

    # If the name is not found in the "From" field, extract it from the "Thanks & regards" section
    if not first_name and not last_name and thanks_match:
        first_name = thanks_match.group(1)
        last_name = thanks_match.group(2)

    # Extract the company name from the email ID (if provided) and remove ".com" or any other characters after the dot (".") symbol
    if emaildata:
        company_name_match = re.search(r'@([^\s.]+)', emaildata)
        if company_name_match:
            company_name = company_name_match.group(1)
            company_name = company_name.split(".")[0]  # Remove ".com" or any other characters after the dot
    else:
        company_name = ""

    # return first_name, last_name, position, phone, email, address, company_name.title()

    return first_name, last_name, phone, emaildata, address, company_name.title()



def custombenchsalesfilewrite(emailfileleads):
    #emailfileleads = dot + str("email_benchsales.csv")
    with open(emailfileleads, 'r', encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        todaydatevalue = dt.today().strftime("%Y-%m-%d")
        for idx, row in enumerate(reader):
            #print(row)
            print('passed')
            html_content = row[3]
            content = html_content

            # Process the email content using the first function
            from_address, last_email_data = process_email_content(content)

            # Extract named entities using the second function
            # first_name, last_name, position, phone, email, address, company_name = extract_named_entities(content)
            first_name, last_name, phone, emaildata, address, company_name = extract_named_entities(content)
            
            
            # Output the extracted data (NER and tabular data)
            print("First Name:", first_name)
            print("Last Name:", last_name)
            print("Mobile:", phone)
            print("Email ID:", emaildata)
            print("Address:", address)
            print("Company Name:", company_name)
            #print("From Address:", from_address)
            #print("Last Email Data:", last_email_data)
            print(idx)
            custombenchdata, created = Custombench.objects.get_or_create(
                    benchfirstname = '',
                    benchlastname = '',
                    benchexperience = '',
                    Rate = '',
                    Position = '',
                    Location = '',
                    Duration = '',
                    benchrelocation = '',
                    Legal_Status = '',
                    benchnoticeperiod = '',
                    benchsalesfirstname = first_name,
                    benchsaleslastname = last_name,
                    benchsalescompany = company_name,
                    benchsalesemail = emaildata,
                    benchsalesmobile = phone,
                    benchsalesaddress = address,
                    Interview_Type = '',
                    Work_Type = '',
                    Remote = '',
                   )
            if created:
                    custombenchdata.save()
                    print('done')


    return first_name, last_name, phone, email, address, company_name.title()


dot='./media/'
# dot = '/var/www/subdomain/whatsappdata/analysis/media/'
from dateutil import parser
def customemailleadsfile(request):
    cache.clear()

    username = "careersales@desss.com"
    password = "!!!H0u$on@77042$$$"

    # SMTP server settings
    smtp_server = "smtp.ionos.com"
    smtp_port = 465
    smtp_username = username
    smtp_password = password

    # IMAP server settings
    imap_server = "imap.ionos.com"
    imap_port = 993
    imap_username = username
    imap_password = password

    # Connect to the IMAP server
    # imap_connection = imaplib.IMAP4_SSL(imap_server, imap_port)
    # imap_connection.login(imap_username, imap_password)
    try:
        # Connect to the IMAP server
        imap_connection = imaplib.IMAP4_SSL(imap_server, imap_port)
        imap_connection.login(imap_username, imap_password)

        # Rest of the code for fetching and processing emails

    except imaplib.IMAP4.abort as e:
        print(f"IMAP connection aborted: {str(e)}")
    except imaplib.IMAP4.error as e:
        print(f"IMAP error occurred: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")


    # Select the INBOX mailbox
    mailbox_name = "INBOX"
    imap_connection.select(mailbox_name)

    # Search for all emails in the INBOX
    _, email_ids = imap_connection.search(None, "ALL")

    # Create a CSV file and write the header

    emailfileleads = dot + str("email_datas.csv")
    csv_file = open(emailfileleads, "w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Subject", "Sender", "Received Time", "Email Body"])
   
    # Iterate over the email IDs in reverse order
    for email_id in reversed(email_ids[0].split()):
        _, email_data = imap_connection.fetch(email_id, "(RFC822)")

        # Parse the email data
        raw_email = email_data[0][1]
        parsed_email = email.message_from_bytes(raw_email)

        # Extract the desired email information
        subject = parsed_email["Subject"]
        sender = parsed_email["From"]
        received_time = parsed_email["Date"]

        # Get the email body
        if parsed_email.is_multipart():
            for part in parsed_email.walk():
                if part.get_content_type() == "text/plain":
                    email_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                # elif part.get_content_type() == "text/html":
                #     email_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            email_body = parsed_email.get_payload(decode=True).decode("utf-8", errors="ignore")
        # Parse the date string using dateutil.parser
        # day = parser.parse(received_time)

        # # Get the 'Date' and 'Time' components as strings with the desired format
        # date_str = day.strftime("%d-%m-%Y")
        # Write the email information to the CSV file
        csv_writer.writerow([subject, sender, received_time, email_body])
        # csv_writer.writerow([subject, sender, date_str, email_body])

    # Close the CSV file
    csv_file.close()

    # Close the IMAP connection
    imap_connection.close()
    imap_connection.logout()
    
    with open(emailfileleads, 'r', encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        todaydatevalue = dt.today().strftime("%Y-%m-%d")
        for row in reader:
            #print(row)
            print('passed')
                        
            customleads, created = Customemailleads.objects.get_or_create(
                todaysdate = todaydatevalue,
                Subject = row[0],
                From = row[1],
                Received_Time = row[2],
                Email_Body = row[3],
                )
            if created:
                customleads.save()
                print('started')
                # email data savings
    # with open(emailfileleads, 'r', encoding="utf-8") as file:
    #     reader = csv.reader(file)
    #     next(reader)  # Advance past the header
    #     todaydatevalue = dt.today().strftime("%Y-%m-%d")
    #     for row in reader:
    #         text = row[3]
    #             # Extracting first name and last name using regex
    #         name_pattern = re.compile(r'From:\s([^<]+)')
    #         match = name_pattern.search(text)

    #         phone_pattern = re.compile(r'Office:\s(\(\d{3}\)\s\d{3}-\d{4})')
    #         phone_match = phone_pattern.search(text)

    #         company_pattern = re.compile(r'From:\s[^<]+\s<([^@]+@[^>]+)>')
    #         company_match = company_pattern.search(text)
    #         address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?)\s+(\d{5})')
    #         address_match = address_pattern.search(text)

    #             # address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?),\s+(\d{5})')
    #             # address_match = address_pattern.search(text)

    #         legalstatus_pattern = re.compile(r'(H1B|No H1B|Green Card|Citizen|Work Visa|Permanent Resident)', re.IGNORECASE)
    #         legalstatus_match = legalstatus_pattern.search(text)

    #         mobile_pattern = re.compile(r'Mob:\s(\d+)')
    #         mobile_match = mobile_pattern.search(text)


    #         try:  
    #             if match:
    #                     name = match.group(1).strip()
    #                     first_name, _, last_name = name.partition(" ")
    #                     email_id = re.search(r'<([^>]+)>', text).group(1)
    #                     # Extracting description using regex
    #                     description_pattern = re.compile(r'Subject:.*?\n\n(.*)', re.DOTALL)
    #                     match = description_pattern.search(text)

    #                     if match:
    #                         description = match.group(1).strip()
    #                     else:
    #                         description = ""

    #                     if phone_match:
    #                         phone_number = phone_match.group(1).strip()
    #                     else:
    #                         phone_number = ""

    #                     if company_match:
    #                         company_email = company_match.group(1).strip()
    #                         # company_name = company_email.split('@')[1].strip()
    #                         # Split email based on "@"
    #                         domain_part = company_email.split('@')[1]
    #                         #  1 means after value of symbol. 0 means before value of symbol.
    #                         # Extract the company name and remove leading/trailing spaces
    #                         company_name = domain_part.split('.')[0].strip().title()
    #                         print(company_name)
    #                         # Remove portion after the last dot in the domain
    #                         # domain_name = '.'.join(domain_part.split('.')[:-1]).title()
    #                         # Check if "Inc" is present in the company name and modify accordingly
                            
    #                     else:
    #                         company_name = ""
    #                         # Check if "Inc" is present in the text and extract the company name accordingly
    #                         # inc_pattern = re.compile(r'\bInc\b', re.IGNORECASE)
    #                         # inc_match = inc_pattern.search(text)
    #                         # if inc_match:
    #                         #     start_index = inc_match.start()
    #                         #     company_name = text[:start_index].strip().title()
    #                         # else:
    #                         #     company_name = ""

    #                     if address_match:
    #                         address = address_match.group(1).strip()
    #                         city = address_match.group(2).strip()
    #                         state = address_match.group(3).strip()
    #                         zipcode = address_match.group(4).strip()
    #                     else:
    #                         address = ""
    #                         city = ""
    #                         state = ""
    #                         zipcode = ""

    #                     if legalstatus_match:
    #                         legalstatus = legalstatus_match.group(0).strip()
    #                     else:
    #                         legalstatus = ""

    #                     if mobile_match:
    #                         mobile_number = mobile_match.group(1).strip()
    #                     else:
    #                         mobile_number = ""



    #                     # Extracting position, location, and duration using regex
    #                     position_pattern = re.compile(r'Position:\s(.*?)\n')
    #                     location_pattern = re.compile(r'Location:\s(.*?)\n')
    #                     duration_pattern = re.compile(r'Duration:\s(.*?)\n')

    #                     position_match = position_pattern.search(text)
    #                     location_match = location_pattern.search(text)
    #                     duration_match = duration_pattern.search(text)

    #                     position = position_match.group(1).strip() if position_match else ""
    #                     location = location_match.group(1).strip() if location_match else ""
    #                     duration = duration_match.group(1).strip() if duration_match else ""

    #             else:
    #                     first_name = ""
    #                     last_name = ""
    #                     email_id = ""
    #                     description = ""
    #                     position = ""
    #                     location = ""
    #                     duration = ""
    #                     phone_number = ""
    #                     company_name = ""

    #                 # Output the extracted fields
    #             print("First Name:", first_name)
    #             print("Last Name:", last_name)
    #             print("Email ID:", email_id)
    #             print("Description:", description)
    #             print("Position:", position)
    #             print("Location:", location)
    #             print("Duration:", duration)
    #             print("Phone Number:", phone_number)
    #             print("Company:", company_name)
    #             print("Address:", address)
    #             print("City:", city)
    #             print("State:", state)
    #             print("Zipcode:", zipcode)
    #             print("Legalstatus:", legalstatus)
    #             print("Mobile Number:", mobile_number)
    #         except:
    #                 first_name = ""
    #                 last_name = ""
    #                 email_id = ""
    #                 description = ""
    #                 position = ""
    #                 location = ""
    #                 duration = ""
    #                 phone_number = ""
    #                 company_name = ""
    #                 address = ""
    #                 city = ""
    #                 state = ""
    #                 zipcode = ""
    #                 legalstatus = ""
    #                 mobile_number = ""



    #         customleadsdata, createds = Customleads.objects.get_or_create(
    #                 leadfirstname = first_name,
    #                 leadlastname = last_name,
    #                 leademail = email_id,
    #                 leadusername = first_name+' '+last_name,
    #                 leadpassword  = 'Desss@123',
    #                 leadcompany = company_name,
    #                 leadphonenumber = phone_number,
    #                 leadaddress = address,
    #                 leadaddress2 = '',
    #                 leadcity = city,
    #                 leadstate = state,
    #                 leadzipcode = zipcode,
    #                 leadposition = position,
    #                 leaddescription = description,
    #                 leadlocation = location,
    #                 leadduration = duration,
    #                 leadlegalstatus = legalstatus,
    #                 leadinterviewtype = '',
    #                 leadworktype = '',
    #                 leadremote = '',
    #                 leadexperience = '',
    #                 leadrate = '',
    #                )
    #         if createds:
    #                 customleadsdata.save()
    #                 print('done')

                    # print('done')
                            # if os.path.exists(filename):
                            #     os.remove(filename)
                            #     print('removed')         
                            
        else:
            print("That file does not exist!")
                #return redirect('customemailleads') 

                        
                        # if os.path.exists(filename):
                        #     os.remove(filename)
                        #     print('removed')
    if os.path.exists(emailfileleads):
        # os.remove(emailfileleads)
        print('removed')
            # return render(request, 'emailbenchsalesdupload.html', {})
        return redirect('customemailleads')    
    # return HttpResponse('ok')
    return redirect('customemailleads')    


# def process_email_content(content):
#     # Load spaCy's English NLP model
#     nlp = spacy.load('en_core_web_sm')

#     # Define the pattern to extract the tabular data
#     pattern = r"(\d+)\s+([^\n]+)\n+(\d+\+?)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)"

#     # Find all matches using the pattern
#     matches = re.findall(pattern, content)

#     # Prepare the extracted tabular data as a list of dictionaries
#     extracted_data = []
#     for match in matches:
#         s_no, technology, exp, visa, location, relocation = match
#         extracted_data.append({
#             "S. No": s_no.strip(),
#             "Technology": technology.strip(),
#             "Exp": exp.strip(),
#             "Visa": visa.strip(),
#             "Location": location.strip(),
#             "Relocation": relocation.strip(),
#             "First Name": "",
#             "Last Name": "",
#             "Mobile": "",
#             "Email ID": "",
#             "Company Name": "",
#             "Company Address": ""
#         })

#     # Process the email text with spaCy for NER
#     doc = nlp(content)

#     # Initialize variables to store the extracted "From" address and the last email data
#     from_address = ""
#     last_email_data = ""

#     # Extract "From" address and the last email data
#     for sent in doc.sents:
#         if "From:" in sent.text:
#             from_address = sent.text.replace("From:", "").strip()
#         last_email_data = sent.text.strip()

#     # Extract named entities (PERSON, PHONE, EMAIL, ORG) from the processed text
#     # Define the regex patterns to extract the required details
#     name_pattern = r'From:\s+(.*?)\s+(.*?)\n'
#     position_pattern = r'\s+(.*?)\s+(.*?)\n\s*(?:[Aa]t|AT|@)\s.*'
#     phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b|\b\d{10}\b'
#     email_pattern = r'[\w\.-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}'
#     address_pattern = r'[A-Za-z]+(?:,[A-Za-z]+)*(?:\s*,\s*\d{5})?\s*,\s*[A-Za-z]+\s*,\s*[A-Za-z]+\s*,\s*\d{5}\b'
#     thanks_pattern = r'(?:Thanks\s*&(?:amp;)?\s*regards|Thanks\s*and\s*Regards),\s*(.*?)\s+([A-Za-z]+)'

#     # Find the matches using the regex patterns
#     name_match = re.search(name_pattern, content)
#     position_match = re.search(position_pattern, content)
#     phone_matches = re.findall(phone_pattern, content)
#     email_match = re.search(email_pattern, content)
#     address_match = re.search(address_pattern, content)
#     thanks_match = re.search(thanks_pattern, content)

#     # Extract the relevant details from the matches if a match is found
#     first_name = name_match.group(1) if name_match else ""
#     last_name = name_match.group(2) if name_match else ""
#     position = position_match.group(1) if position_match else ""
#     phone = next((num for num in phone_matches if len(num) == 10), "")
#     emaildatas = email_match.group() if email_match else ""
#     address = address_match.group() if address_match else ""

#     # If the name is not found in the "From" field, extract it from the "Thanks & regards" section
#     if not first_name and not last_name and thanks_match:
#         first_name = thanks_match.group(1)
#         last_name = thanks_match.group(2)

#     # Extract the company name from the email ID (if provided) and remove ".com" or any other characters after the dot (".") symbol
#     if emaildatas:
#         company_name_match = re.search(r'@([^\s.]+)', emaildatas)
#         if company_name_match:
#             company_name = company_name_match.group(1)
#             company_name = company_name.split(".")[0]  # Remove ".com" or any other characters after the dot
#     else:
#         company_name = ""

#     # Output the extracted data (NER and tabular data)
#     print("First Name:", first_name)
#     print("Last Name:", last_name)
#     print("Mobile:", phone)
#     print("Email ID:", emaildatas)
#     print("Address:", address)
#     print("Company Name:", company_name)

#     return extracted_data, first_name, last_name, phone, emaildatas, address, company_name


def custombenchsalesfile(request):
    # cache.clear()

    username = "benchsales@desss.com"
    password = "!!!H0u$on@77042$$$"

    # SMTP server settings
    smtp_server = "smtp.ionos.com"
    smtp_port = 465
    smtp_username = username
    smtp_password = password

    # IMAP server settings
    imap_server = "imap.ionos.com"
    imap_port = 993
    imap_username = username
    imap_password = password

    # Connect to the IMAP server
    # imap_connection = imaplib.IMAP4_SSL(imap_server, imap_port)
    # imap_connection.login(imap_username, imap_password)
    try:
        # Connect to the IMAP server
        imap_connection = imaplib.IMAP4_SSL(imap_server, imap_port)
        imap_connection.login(imap_username, imap_password)

        # Rest of the code for fetching and processing emails

    except imaplib.IMAP4.abort as e:
        print(f"IMAP connection aborted: {str(e)}")
    except imaplib.IMAP4.error as e:
        print(f"IMAP error occurred: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

    # Select the INBOX mailbox
    mailbox_name = "INBOX"
    imap_connection.select(mailbox_name)

    # Search for all emails in the INBOX
    _, email_ids = imap_connection.search(None, "ALL")

    # Create a CSV file and write the header

    emailfileleads = dot + str("email_benchsales.csv")
    csv_file = open(emailfileleads, "w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Subject", "Sender", "Received Time", "Email Body", "Email HTML"])

    # Iterate over the email IDs in reverse order
    for email_id in reversed(email_ids[0].split()):
        _, email_data = imap_connection.fetch(email_id, "(RFC822)")

        # Parse the email data
        raw_email = email_data[0][1]
        parsed_email = email.message_from_bytes(raw_email)

        # Extract the desired email information
        subject = parsed_email["Subject"]
        sender = parsed_email["From"]
        received_time = parsed_email["Date"]

        # # Get the email body
        # if parsed_email.is_multipart():
        #     for part in parsed_email.walk():
        #         if part.get_content_type() == "text/plain":
        #             email_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
        #             break
        # else:
        #     email_body = parsed_email.get_payload(decode=True).decode("utf-8", errors="ignore")
               # Initialize variables for email body and HTML content
        email_body = ""
        email_html = ""
         # Get the email body
        if parsed_email.is_multipart():
            for part in parsed_email.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    email_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif content_type == "text/html":
                    email_html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        # else:
        #     if content_type == "text/plain":
        #         email_body = parsed_email.get_payload(decode=True).decode("utf-8", errors="ignore")
        #     elif content_type == "text/html":
        #         email_html = parsed_email.get_payload(decode=True).decode("utf-8", errors="ignore")
            #email_body = parsed_email.get_payload(decode=True).decode("utf-8", errors="ignore")

        else:
            email_body = parsed_email.get_payload(decode=True).decode("utf-8", errors="ignore")

        if  email_body == "":
            cleantext = BeautifulSoup(email_html, "lxml").text
            email_body = cleantext
        # Write the email information to the CSV file
        csv_writer.writerow([subject, sender, received_time, email_body, email_html])

    # Close the CSV file
    csv_file.close()

    # Close the IMAP connection
    imap_connection.close()
    imap_connection.logout()
    
    with open(emailfileleads, 'r', encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        todaydatevalue = dt.today().strftime("%Y-%m-%d")
        for row in reader:
            #print(row)
            print('passed')
                        
            customleadsa, created = Custombenchsales.objects.get_or_create(
                bstodaysdate = todaydatevalue,
                bsSubject = row[0],
                bsFrom = row[1],
                bsReceived_Time = row[2],
                bsEmail_Body = row[3],
                bsEmail_Bodyhtml = row[4],
                )
            if created:
                customleadsa.save()
                print('done')
                #custombenchsalesfilewrite(emailfileleads)
                # content = row[3]

                # # Process the email content using the first function
                # from_address, last_email_data = process_email_content(content)

                # # Extract named entities using the second function
                # # first_name, last_name, position, phone, email, address, company_name = extract_named_entities(content)
                # first_name, last_name, phone, emaildata, address, company_name = extract_named_entities(content)


                # # Output the extracted data (NER and tabular data)
                # print("First Name:", first_name)
                # print("Last Name:", last_name)
                # print("Mobile:", phone)
                # print("Email ID:", emaildata)
                # print("Address:", address)
                # print("Company Name:", company_name)
                # custombenchdata, created = Custombench.objects.get_or_create(
                #     benchfirstname = '',
                #     benchlastname = '',
                #     benchexperience = '',
                #     Rate = '',
                #     Position = '',
                #     Location = '',
                #     Duration = '',
                #     benchrelocation = '',
                #     Legal_Status = '',
                #     benchnoticeperiod = '',
                #     benchsalesfirstname = first_name,
                #     benchsaleslastname = last_name,
                #     benchsalescompany = company_name,
                #     benchsalesemail = emaildata,
                #     benchsalesmobile = phone,
                #     benchsalesaddress = address,
                #     Interview_Type = '',
                #     Work_Type = '',
                #     Remote = '',
                #    )
                # if created:
                #     custombenchdata.save()
                #     print('done')



                #return redirect('custombenchsales') 
                            # if os.path.exists(filename):
                            #     os.remove(filename)
                            #     print('removed')         
                            
            else:
                print("That file does not exist!")
                # return redirect('custombenchsales') 

                        
                        # if os.path.exists(filename):
                        #     os.remove(filename)
                        #     print('removed')
    if os.path.exists(emailfileleads):
        # os.remove(emailfileleads)
        print('removed')
            # return render(request, 'emailbenchsalesdupload.html', {})
        return redirect('custombenchsales')    
    # return HttpResponse('ok')
    return redirect('custombenchsales')  

def index(requests):
    documents = whatsapp.objects.all()
    for obj in documents:
        baseurls = obj.chat
    print(baseurls)
    data = []
    #conversation = 'whatsapp-chat-data.txt'
    conversation = dot + str(baseurls)
    print(conversation)
    with open(conversation, encoding="utf-8") as fp:
        fp.readline()
        messageBuffer = []
        date, time, author = None, None, None
        while True:
            line = fp.readline()
            if not line:
                break
            line = line.strip()
            if date_time(line):
                if len(messageBuffer) > 0:
                    data.append([date, time, author, ' '.join(messageBuffer)])
                    messageBuffer.clear()
                    date, time, author, message = getDatapoint(line)
                    messageBuffer.append(message)
                else:
                    messageBuffer.append(line)
    df = pd.DataFrame(data, columns=["Date", 'Time', 'Author', 'Message'])
    df['Date'] = pd.to_datetime(df['Date'])
    df.to_csv(dot+'media/data.csv', index = False)
    filename = dot + str(baseurls)
    with open(filename, 'r', encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        for row in reader:
            print(row)
            print('passed')
                        
            lead, created = Customemailleads.objects.get_or_create(
                firstname = row[0],
                lastname = row[1],
                email = row[2],
                username = row[3],
                )
            if created:
                lead.save()
                print('done')
                            # if os.path.exists(filename):
                            #     os.remove(filename)
                            #     print('removed')         
                            
            else:
                print("That file does not exist!")
                        
                        # if os.path.exists(filename):
                        #     os.remove(filename)
                        #     print('removed')
    if os.path.exists(filename):
        os.remove(filename)
        print('removed')
            # return render(request, 'emailbenchsalesdupload.html', {})
        return redirect('emailnewleads')
    # return HttpResponse('hello world')
    return redirect('emailnewleads')
# 

import re
import pandas as pd
import csv

import os


####


# def emaillead_upload_txt(request):
#     if request.method == 'POST':
#         form = CustomizeEmailLeadsForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             # return redirect('index')
#             documents = CustomizeEmailLeads.objects.all()
#             for obj in documents:
#                 baseurls = obj.Fileupload
#             print(baseurls)
            
#             #filename = "test1.txt"
#             filename = dot + str(baseurls)

            
#             # Open the text file for reading
#             with open(filename, encoding = 'utf8') as file:
#                 # Create a CSV writer object
#                 csv_writer = csv.writer(open(dot+'media/emailleads.csv', 'w', newline='', encoding="utf-8"))

#                 # Write the column names to the CSV file
#                 column_names = ["First Name", "Last Name", "Email", "User Name", "Password", "Company", "Phone Number",
#                                 "Address", "Address 2", "City", "State", "Zip Code", "Occupation", "Opportunity Description"]
#                 csv_writer.writerow(column_names)

#                 # Process each line in the text file
#                 lines = file.readlines()
#                 i = 0
#                 while i < len(lines):
#                     # Check if the line starts with "&&&&" to skip any separator lines
#                     if lines[i].strip().startswith("&&&&"):
#                         i += 1
#                         continue

#                     # Split the line by '|' symbol
#                     data = lines[i].strip().split('|')

#                     # Ensure that the data contains all the required columns
#                     if len(data) >= 13:
#                         # Extract the fields from the data
#                         first_name = data[0]
#                         last_name = data[1]
#                         email = data[2]
#                         user_name = data[3]
#                         password = data[4]
#                         company = data[5]
#                         phone_number = data[6]
#                         address = data[7]
#                         address2 = data[8]
#                         city = data[9]
#                         state = data[10]
#                         zip_code = data[11]
#                         occupation = data[12]

#                         # Combine the remaining elements as the OPPORTUNITY DESCRIPTION
#                         opportunity_description = '|'.join(data[13:])

#                         # Process the OPPORTUNITY DESCRIPTION until '&&&&' is found or end of file
#                         i += 1
#                         while i < len(lines) and not lines[i].strip().startswith("&&&&"):
#                             opportunity_description += ' ' + lines[i].strip()
#                             i += 1

#                         # Write the extracted data to the CSV file
#                         csv_writer.writerow([first_name, last_name, email, user_name, password, company, phone_number, address,
#                                             address2, city, state, zip_code, occupation, opportunity_description.strip()])
                        
#                          # Write the extracted data to the CSV file and save to database
#                         lead, created =  Emailsample.objects.get_or_create(
#                             firstname=first_name,
#                             lastname=last_name,
#                             email=email,
#                             username=user_name,
#                             password=password,
#                             company=company,
#                             phonenumber=phone_number,
#                             address=address,
#                             address2=address2,
#                             city=city,
#                             state=state,
#                             zipcode=zip_code,
#                             occupation=occupation,
#                             description=opportunity_description.strip()
                            
#                         )
#                         print('done')
#                         if created:
#                             lead.save()
#                     # Move to the next line
#                     i += 1

#             print("CSV conversion completed successfully.")


#             # Write the extracted data to the CSV file and save to database
#             # lead, created =  Emailsample.objects.get_or_create(
#             #     firstname=first_name,
#             #     lastname=last_name,
#             #     email=email,
#             #     username=user_name,
#             #     password=password,
#             #     company=company,
#             #     phonenumber=phone_number,
#             #     address=address,
#             #     address2=address2,
#             #     city=city,
#             #     state=state,
#             #     zipcode=zip_code,
#             #     occupation=occupation,
#             #     description=opportunity_description.strip()
                
#             # )
#             # print('done')
#             # if created:
#             #     lead.save()
#             # lead.save()
              
#             if os.path.exists(filename):
#                         os.remove(filename)
#                         print('removed')
#             else:
#                 print("That file does not exist!")
#             # return render(request, 'emailleadupload.html', {})
#             return redirect('emailnewleads')
            
#         # return render(request, 'emailleadupload.html', {})
#         return redirect('emailnewleads')
#     else:
#         form = CustomizeEmailLeadsForm()
#         documents = CustomizeEmailLeads.objects.all()
#     return render(request, 'emailleadupload.html', {
#         'form': form
#     })


def emaillead_upload_txt(request):
    if request.method == 'POST':
        form = CustomizeEmailLeadsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # return redirect('index')
            documents = CustomizeEmailLeads.objects.all()
            for obj in documents:
                baseurls = obj.Fileupload
            print(baseurls)
            
            #filename = "test1.txt"
            filename = dot + str(baseurls)
            with open(filename, 'r', encoding="utf-8") as file:
                    reader = csv.reader(file)
                    next(reader)  # Advance past the header
                    for row in reader:
                        print(row)
                        print('passed')
                        
                        lead, created = Emailsample.objects.get_or_create(
                            firstname = row[0],
                            lastname = row[1],
                            email = row[2],
                            username = row[3],
                            password = row[4],
                            company = row[5],
                            phonenumber = row[6],
                            address = row[7],
                            address2 = row[8],
                            city = row[9],
                            state = row[10],
                            zipcode = row[11],
                            occupation = row[12],
                            description = row[13]
                            )
                        if created:
                            lead.save()
                            print('done')
                            # if os.path.exists(filename):
                            #     os.remove(filename)
                            #     print('removed')
                            
                            
                        else:
                           print("That file does not exist!")
                        
                        # if os.path.exists(filename):
                        #     os.remove(filename)
                        #     print('removed')
            if os.path.exists(filename):
                os.remove(filename)
                print('removed')
            # return render(request, 'emailbenchsalesdupload.html', {})
            return redirect('emailnewleads')
    else:
        form= CustomizeEmailLeadsForm()
        documents = CustomizeEmailLeads.objects.all()
    return render(request, 'emailleadupload.html', {
        'form': form
    })


def emailbenchsalesupload(request):
    if request.method == 'POST':
        benchsalesform = CustomizeBenchsalesLeadsForm(request.POST, request.FILES)
        if benchsalesform.is_valid():
            benchsalesform.save()
            # return redirect('index')
            documents = CustomizeBenchsalesLeads.objects.all()
            for obj in documents:
                baseurls = obj.BenchsalesFile
            print(baseurls)
            
            #filename = "test1.txt"
            filename = dot + str(baseurls)
            with open(filename, 'r', encoding="utf-8") as file:
                    reader = csv.reader(file)
                    next(reader)  # Advance past the header
                    for row in reader:
                        print(row)
                        print('passed')
                        
                        # datetime_str = row[0]
                        # date_str = datetime_str.split()[0]
                        # time_str = datetime_str.split()[1]
                        
                        # if row[2] == '<Media omitted>' or row[2] == 'Waiting for this message':
                        #     continue
                        # else:
                        benchsales, created = Emailbenchsales.objects.get_or_create(
                            First_Name= row[0],
                            Last_Name= row[1],
                            Experience= row[2],
                            Current_Location= row[3],
                            Technology= row[4],
                            Relocation= row[5],
                            Visa= row[6],
                            Notice_Period= row[7],
                            Benchsales_First_Name= row[8],
                            Benchsales_Last_Name= row[9],
                            Benchsales_Company= row[10],
                            Benchsales_Email= row[11],
                            Benchsales_Mobile= row[12],
                            Benchsales_Address= row[13]
                            )
                        if created:
                            benchsales.save()
                            print('done')
                            # if os.path.exists(filename):
                            #     os.remove(filename)
                            #     print('removed')
                            
                            
                        else:
                           print("That file does not exist!")
                        
                        # if os.path.exists(filename):
                        #     os.remove(filename)
                        #     print('removed')
            if os.path.exists(filename):
                os.remove(filename)
                print('removed')
            # return render(request, 'emailbenchsalesdupload.html', {})
            return redirect('benchsales')
    else:
        benchsalesform= CustomizeBenchsalesLeadsForm()
        documents = CustomizeBenchsalesLeads.objects.all()
    return render(request, 'emailbenchsalesdupload.html', {
        'benchsalesform': benchsalesform
    })

def upload_txt(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            option = form.cleaned_data['option']
            # chat = form.cleaned_data['file']
            form.save()
            
            documents = whatsapp.objects.all()  # Assuming the model name is "Whatsapp"
            for obj in documents:
                baseurls = obj.chat
            print(baseurls)

            if option == 'whatsapp':
                filename = dot + str(baseurls)  # It's unclear what 'dot' represents, please make sure it is defined
                
                pat = re.compile(r'^(\d+\/\d+\/\d\d.*?)(?=^^\d+\/\d+\/\d\d\,\*?)', re.S | re.M)
                with open(filename, encoding='utf8') as raw:
                    data = [m.group(1).strip().replace('\n', ' ') for m in pat.finditer(raw.read())]
                
                sender = []
                message = []
                datetime = []
                
                for row in data:
                    datetime.append(row.split(' - ')[0])

                    try:
                        s = re.search('M - (.*?):', row).group(1)
                        sender.append(s)
                    except:
                        sender.append('')

                    try:
                        message.append(row.split(': ', 1)[1])
                    except:
                        message.append('')

                df = pd.DataFrame(zip(datetime, sender, message), columns=['timestamp', 'sender', 'message'])
                df['timestamp'] = pd.to_datetime(df.timestamp, format='%m/%d/%y, %I:%M %p')

                df = df[df.sender != ''].reset_index(drop=True)
                df.to_csv(dot + 'media/data.csv', index=False)
                print('ok')

                with open(dot + 'media/data.csv', 'r', encoding="utf-8") as file:
                    reader = csv.reader(file)
                    next(reader)  # Advance past the header
                    for row in reader:
                        print(row)
                        print('passed')
                        
                        datetime_str = row[0]
                        date_str = datetime_str.split()[0]
                        time_str = datetime_str.split()[1]
                        
                        if row[2] == '<Media omitted>' or row[2] == 'Waiting for this message':
                            continue
                        else:
                            film, created = Film.objects.get_or_create(
                                date=date_str,
                                title=time_str,
                                year=row[1],
                                filmurl=row[2]
                            )
                            if created:
                                film.save()
                
                if os.path.exists(filename):
                    os.remove(filename)
                else:
                    print("That file does not exist!")
                
                return render(request, 'form_upload.html', {})
            
            # elif option == 'email benchsales':

            #     try:
            #         filename = dot + str(baseurls)
            #         # Define the column names
            #         fieldnames = ['Reference date', 'Reference time', 'Reference Mobile Number', 'Reference Details', 'User date', 'User time', 'User Mobile Number', 'User Details',]

            #         # Read the text file
            #         # with open('input.txt', 'r') as file:
            #         with open(filename, 'r',  encoding="utf-8") as file:
            #             content = file.read()

            #         # Split the content based on '&&&' to get individual rows
            #         rows = content.split('&&&')

            #         # Extract the initial "date and time" and "Mobile Number"
            #         initial_line = rows[0].strip().split('\n')[0]
            #         date_time, mobile_number = initial_line.split(' - ')
            #         date, time = date_time.split(',')

            #         # Extract the mobile number till the ":" character
            #         try:
            #             mobile_numbers = mobile_number[:mobile_number.index(':')].strip()
            #         # except ValueError:
            #         except Exception as e:
            #             print(e)
            #             mobile_numbers = mobile_number.strip()
            #         formatted_date = dt.strptime(date.strip(), "%m/%d/%y").strftime("%Y-%m-%d")
            #         # Prepare the output CSV file
            #         with open(dot + 'media/modified_data.csv', 'w', newline='', encoding="utf-8") as file:
            #             writer = csv.DictWriter(file, fieldnames=fieldnames)
            #             writer.writeheader()

            #             # Iterate over each row and write the values
            #             for row in rows:
            #                 lines = row.strip().split('\n')
            #                 # messages = '\n'.join(lines[0:]).replace('&&&', '')
            #                 user_details = '\n'.join(lines[0:]).replace('&&&', '')


            #                 # Remove mobile number from the reference details
            #                 reference_details = mobile_number[mobile_number.index(':')+1:].strip()

            #                 # Write the values to the CSV file
            #                 # writer.writerow({'date': date.strip(), 'time': time.strip(), 'Mobile Number': mobile_numbers, 'Messages': messages, 'Reference Details': user_details})
            #                 #write.writerow({'Reference date':date.strip(), 'Reference time':time.strip(), 'Reference Mobile Number':mobile_numbers, 'Reference Details':messages, 'User date':date.strip(), 'User time';time.strip(), 'User Mobile Number':mobile_numbers, 'User Details':user_details})
            #                 writer.writerow({'Reference date': formatted_date, 'Reference time': time.strip(), 'Reference Mobile Number': mobile_numbers, 'Reference Details': reference_details, 'User date': formatted_date, 'User time': time.strip(), 'User Mobile Number': mobile_numbers, 'User Details': user_details})
            #         # # Open the input CSV file
            #         with open(dot + 'media/modified_data.csv', 'r', encoding="utf-8") as file:
            #             reader = csv.DictReader(file)

            #             # Open the output CSV file
            #             with open(dot + 'media/final_modified_data.csv', 'w', newline='', encoding="utf-8") as outfile:
            #                 fieldnames = reader.fieldnames
            #                 writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            #                 writer.writeheader()

            #                 # Iterate over each row and process the data
            #                 for row in reader:
            #                     user_details = row['User Details']

            #                     # Remove the unwanted portion from User Details if it exists
            #                     if ':' in user_details:
            #                         user_details = user_details[user_details.index(':')+1:].strip()
            #                         user_details = user_details[user_details.index(':')+1:].strip()
            #                     elif ':' in user_details:
            #                         user_details = user_details[user_details.index(':')+1:].strip()
            #                         user_details = user_details[user_details.index(':')+1:].strip()
            #                         user_details = user_details[user_details.index(':')+1:].strip()
            #                     else:
            #                         # user_details = ''
            #                         user_details = user_details

            #                     # Update the row with the modified User Details
            #                     row['User Details'] = user_details

            #                     # Write the row to the output CSV file
            #                     writer.writerow(row)

            #         df = pd.read_csv(dot + 'media/final_modified_data.csv', encoding='utf8')
            #         # df = df[df['message'].notna()]
            #         # df = pd.read_csv(dot + 'media/modified_data.csv', encoding='utf8')
            #         # df = df[df['message'].notna()]
                    
            #         for _, row in df.iterrows():
            #             # datetime_str = row[0]
            #             # date_str = datetime_str.split()[0]
            #             # time_str = datetime_str.split()[1]
            #             if row[7] == '<Media omitted>' or row[7] == 'Waiting for this message':
            #                 continue
            #             else:
            #                 emaillead, created = Emaillead.objects.get_or_create(
            #                     userdate = row[0],
            #                     usertime = row[1],
            #                     usermob = row[2],
            #                     userdetails = row[3],
            #                     emailuserdate = row[4],
            #                     emailusertime = row[5],
            #                     emailusermob = row[6],
            #                     emailuserdetails = row[7]
            #                 # date=date_str,
            #                 # title=time_str,
            #                 # year=row[1],
            #                 # filmurl=row[2]
            #                    )
            #                 print('done')
            #                 if created:
            #                     emaillead.save()
                    
            #         if os.path.exists(filename):
            #             os.remove(filename)
            #         else:
            #             print("That file does not exist!")
                    
            #         return render(request, 'form_upload.html', {})
            #     except Exception as e:
            #         print(e)
            #         error_message = "Please upload a valid file"
            #         return render(request, 'form_upload.html', {'errortext':error_message})
            elif option == 'email opportunities':

                try:
                    filename = dot + str(baseurls)
                    print(filename)
                    # Define the column names
                    fieldnames = ['Reference date', 'Reference time', 'Reference Mobile Number', 'Reference Details', 'User date', 'User time', 'User Mobile Number', 'User Details',]

                    # Read the text file
                    # with open('input.txt', 'r') as file:
                    with open(filename, 'r', encoding="utf-8") as file:
                        content = file.read()

                    # Split the content based on '&&&' to get individual rows
                    rows = content.split('&&&')

                    # Extract the initial "date and time" and "Mobile Number"
                    initial_line = rows[0].strip().split('\n')[0]
                    date_time, mobile_number = initial_line.split(' - ')
                    date, time = date_time.split(',')

                    # Extract the mobile number till the ":" character
                    try:
                        mobile_numbers = mobile_number[:mobile_number.index(':')].strip()
                    # except ValueError:
                    except Exception as e:
                        print(e)
                        mobile_numbers = mobile_number.strip()
                    formatted_date = dt.strptime(date.strip(), "%m/%d/%y").strftime("%Y-%m-%d")
                    # Prepare the output CSV file
                    with open(dot + 'media/emailmodified_data.csv', 'w', newline='', encoding="utf-8") as file:
                        writer = csv.DictWriter(file, fieldnames=fieldnames)
                        writer.writeheader()

                        # Iterate over each row and write the values
                        for row in rows:
                            lines = row.strip().split('\n')
                            # messages = '\n'.join(lines[0:]).replace('&&&', '')
                            user_details = '\n'.join(lines[0:]).replace('&&&', '')


                            # Remove mobile number from the reference details
                            reference_details = mobile_number[mobile_number.index(':')+1:].strip()

                            # Write the values to the CSV file
                            # writer.writerow({'date': date.strip(), 'time': time.strip(), 'Mobile Number': mobile_numbers, 'Messages': messages, 'Reference Details': user_details})
                            #write.writerow({'Reference date':date.strip(), 'Reference time':time.strip(), 'Reference Mobile Number':mobile_numbers, 'Reference Details':messages, 'User date':date.strip(), 'User time';time.strip(), 'User Mobile Number':mobile_numbers, 'User Details':user_details})
                            writer.writerow({'Reference date': formatted_date, 'Reference time': time.strip(), 'Reference Mobile Number': mobile_numbers, 'Reference Details': reference_details, 'User date': formatted_date, 'User time': time.strip(), 'User Mobile Number': mobile_numbers, 'User Details': user_details})
                    # Open the input CSV file
                    with open(dot + 'media/emailmodified_data.csv', 'r', encoding="utf-8") as file:
                        reader = csv.DictReader(file)

                        # Open the output CSV file
                        with open(dot + 'media/final_emailmodified_data.csv', 'w', newline='', encoding="utf-8") as outfile:
                            fieldnames = reader.fieldnames
                            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                            writer.writeheader()

                            # Iterate over each row and process the data
                            for row in reader:
                                user_details = row['User Details']

                                # Remove the unwanted portion from User Details if it exists
                                if ':' in user_details:
                                    user_details = user_details[user_details.index(':')+1:].strip()
                                    user_details = user_details[user_details.index(':')+1:].strip()
                                elif ':' in user_details:
                                    user_details = user_details[user_details.index(':')+1:].strip()
                                    user_details = user_details[user_details.index(':')+1:].strip()
                                else:
                                    # user_details = ''
                                    user_details = user_details

                                # Update the row with the modified User Details
                                row['User Details'] = user_details

                                # Write the row to the output CSV file
                                writer.writerow(row)

                    df = pd.read_csv(dot + 'media/final_emailmodified_data.csv', encoding='utf8')
                    # df = pd.read_csv(dot + 'media/emailmodified_data.csv', encoding='utf8')
                    # df = df[df['message'].notna()]
                    
                    for _, row in df.iterrows():
                        # datetime_str = row[0]
                        # date_str = datetime_str.split()[0]
                        # time_str = datetime_str.split()[1]
                        if row[7] == '<Media omitted>' or row[7] == 'Waiting for this message':
                            continue
                        else:
                            emailleadoppurtunities, created = Emailleadoppurtunities.objects.get_or_create(
                                refuserdate = row[0],
                                refusertime = row[1],
                                refusermob = row[2],
                                refuserdetails = row[3],
                                refemailuserdate = row[4],
                                refemailusertime = row[5],
                                refemailusermob = row[6],
                                refemailuserdetails = row[7]
                            # date=date_str,
                            # title=time_str,
                            # year=row[1],
                            # filmurl=row[2]
                            )
                            print('done')
                            if created:
                                emailleadoppurtunities.save()
                    
                    if os.path.exists(filename):
                        os.remove(filename)
                    else:
                        print("That file does not exist!")
                    
                    return render(request, 'form_upload.html', {})
                except Exception as e:
                    print(e)
                    error_message = "Please upload a valid file"
                    return render(request, 'form_upload.html', {'errortext':error_message})
        else:
            form = UploadFileForm()
            documents = whatsapp.objects.all()  # Assuming the model name is "Whatsapp"
        
        return render(request, 'form_upload.html', {'form': form})
    
    return render(request, 'form_upload.html', {})

        
def indexhtml(request):
    filmes = Film.objects.all()
    return render(request, 'films.html', { 'filmes': filmes })

# def retrieve(request):
#     details=Film.objects.all().order_by('-id')
#     return render(request,'retrieve.html',{'details':details})

def edit(request,id):
    object=Film.objects.get(id=id)

   
    return render(request,'edit.html',{'object':object,}) #'sources': sources})
from django.http import HttpResponseRedirect

def update(request,id):
    my_model = get_object_or_404(Film, id=id)
    if request.method == 'POST':
        form = FilmForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            if 'save_home' in request.POST:
                return redirect('home')
            elif 'save_next' in request.POST:
                try:
                    next_model = Film.objects.filter(id__gt=id).filter(dropdownlist='New').order_by('id')[0]
                    return redirect('edit', id=next_model.id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                # for id in delete_idd:
                    # product = Film.object.get(pk=id)
                    # obj = get_object_or_404(Film, id = id)
                    # obj.delete()
                # id = request.POST.get('idd')
                # id = id
                # obj = get_object_or_404(Film, id=id)
                # obj.delete()
                try:

                    next_model = Film.objects.filter(id__gt=id).filter(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Film, id=id)
                    id=next_model.id
                    
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('edit', id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                # try:

                #     next_model = Film.objects.filter(id__gt=id).filter(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                #     obj = get_object_or_404(Film, id=id)
                    
                #     context ={}
 
                #     # fetch the object related to passed id
                #     obj = get_object_or_404(Film, id = id)
                
                #     id=next_model.id
                #     if request.method =="POST":
                #         # delete object
                #         obj.delete()
                #         print('deleteworking')
                #         return redirect('edit', id)
                    
                #     # obj = get_object_or_404(Film, id=id)
                #     # obj.delete()
                #     return redirect('edit', id)
                # except IndexError:
                #     return render(request, 'navigation.html')
                try:
                    next_model = Film.objects.filter(id__gt=id).filter(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Film, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('edit', id)
                except IndexError:
                    obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return render(request, 'navigation.html')
    else:
        form = FilmForm(instance=my_model)
    
    # my_model = Film.objects.get(id=id)
    # if request.method == 'POST':
    #     form = FilmForm(request.POST, instance=my_model)
    #     if form.is_valid():
    #         form.save()
    #         if 'save_home' in request.POST:
    #             return redirect('home')
    #         elif 'save_next' in request.POST:
    #             try:
    #                 next_model = Film.objects.filter(id__gt=id).order_by('id')[0]
    #                 return redirect('edit',id=next_model.id)
    #             except Film.DoesNotExist:
    #                 pass
    # else:
    #     form = FilmForm(instance=my_model)

    # object=Film.objects.get(id=id)
    # print(object)
    # form=FilmForm(request.POST,instance=object)
    # if request.method == 'POST':
    #     if form.is_valid():
    #         form.save()
    #         # object=Film.objects.all()
    #         return redirect('home')

            # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            # return redirect(request.META['HTTP_REFERER'])
    # return redirect('retrieve')
    # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return redirect(request.META['HTTP_REFERER'])

def leadedit(request,id):
    object=Film.objects.get(id=id)

   
    return render(request,'leadsedit.html',{'object':object,})

def emailsampleleadedit(request,id):
    object=Emailsample.objects.get(id=id)

   
    return render(request,'emailsampleedit.html',{'object':object,})

# def emailleadedit(request,id):
#     object=Emaillead.objects.get(id=id)

   
#     return render(request,'emailleadedit.html',{'object':object,})

def customemailleadsedit(request,id):
    object=Customemailleads.objects.get(id=id)

   
    return render(request,'customemailleadview.html',{'object':object,})


def customleadopportunitiesview(request,id):
    object=Customemailleads.objects.get(id=id)

   
    return render(request,'customleadopportunitiesview.html',{'object':object,})
# def customemailleadsedits(request,id):
#     object=Customleads.objects.get(id=id)

   
#     return render(request,'customemailleadsedits.html',{'object':object,})


# def custombenchsalesedits(request,id):
#     object=Custombenchsales.objects.get(id=id)

   
#     return render(request,'custombenchsalesedits.html',{'object':object,})


def custombenchsalesedit(request,id):
    object=Custombenchsales.objects.get(id=id)

   
    return render(request,'custombenchsalesview.html',{'object':object,})

def emailbenchsalesedit(request,id):
    object=Emailbenchsales.objects.get(id=id)

   
    return render(request,'emailbenchsalesedit.html',{'object':object,})

def emailleadoppurtunitiesedit(request,id):
    object=Emailleadoppurtunities.objects.get(id=id)

   
    return render(request,'emailleadoppedit.html',{'object':object,})

# def leadupdate(request,id):
#     my_model = get_object_or_404(Film, id=id)
#     if request.method == 'POST':
#         form = FilmForm(request.POST, instance=my_model)
#         if form.is_valid():
#             form.save()
#             # delete_idd=request.POST.get('id')
#             if 'save_home' in request.POST:
#                 return redirect('leads')
#             elif 'save_next' in request.POST:
#                 try:
#                     next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').order_by('id')[0]
#                     return redirect('leadedit', id=next_model.id)
#                 except IndexError:
#                     return render(request, 'navigation.html')
#             elif 'save_continue' in request.POST:
#                 return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
#             elif 'save_convert' in request.POST:
#                 status = Film.objects.get(id=id)
#                 print(status)
#                 status.checkstatus^= 1
#                 status.save()
#                 try:
#                     next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
#                     return redirect('leadedit', id=next_model.id)
#                 except IndexError:
#                     return render(request, 'navigation.html')
                
#             elif 'delete_d' in request.POST:
#                 # snippet_ids=request.POST.getlist('ids[]')
#                 print(id)
#                 try:

#                     next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
#                     obj = get_object_or_404(Film, id=id)
#                     id=next_model.id
                    
#                     # obj = get_object_or_404(Film, id=id)
#                     obj.delete()
#                     return redirect('leadedit', id)
#                 except IndexError:
#                     return render(request, 'navigation.html')
#             elif 'delete_dynamic' in request.POST:
        
#                 try:
#                     next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
#                     obj = get_object_or_404(Film, id=id)
#                     id = next_model.id
#                     obj.delete()
#                     return redirect('leadedit', id)
#                 except IndexError:
#                     obj = get_object_or_404(Film, id=id)
#                     obj.delete()
#                     return render(request, 'navigation.html')
               
#     else:
#         form = FilmForm(instance=my_model)
#     return redirect(request.META['HTTP_REFERER'])

def delete(request, id):

    context ={}
 
    # fetch the object related to passed id
    obj = get_object_or_404(Film, id = id)
 
 
    if request.method =="POST":
        # delete object
        obj.delete()
     
        return redirect('home')
 
    return render(request, "delete.html", context)

import requests

def leadupdate(request,id):
    my_model = get_object_or_404(Film, id=id)
    if request.method == 'POST':
        form = FilmForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            # delete_idd=request.POST.get('id')
            if 'save_home' in request.POST:
                return redirect('leads')
            elif 'save_next' in request.POST:
                try:
                    next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').order_by('id')[0]
                    return redirect('leadedit', id=next_model.id)
                    # return redirect('leads')
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'save_convert' in request.POST:
                status = Film.objects.get(id=id)
                print(status)
                status.checkstatus^= 1
                status.save()
                try:
                    next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    return redirect('leadedit', id=next_model.id)
                
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                try:
                    next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Film, id=id)
                    id=next_model.id
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('leadedit', id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                try:
                    # next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Film, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('leadedit', id)
                except IndexError:
                    obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return render(request, 'navigation.html')
            elif 'chiliadstaffingapi' in request.POST:
                # Call first A
                id = my_model.id
                if id==id:
                    year = my_model.year
                    filmurl = my_model.filmurl
                    # replacements = [('%', ''), ('&', 'and'), ('∷', '')]

                    # for char, replacement in replacements:
                    #     if char in filmurl:
                    #         filmurl = filmurl.replace(char, replacement)

                    # print(filmurl)
                    # originaldata = re.sub(r'\W+', '', filmurl)
                    # print(originaldata)
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', filmurl)
                    
                    title = my_model.title
                    url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=lead&phone={year}&message={originaldata}&date={title}"
                    # api_params = {
                    #     'action': 'lead',
                    #     'phone': my_model.year,
                    #     'message': my_model.filmurl,
                    #     'date': my_model.title,
                    # }
                    # response = requests.get(api_url, params=api_params)
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                    return redirect('leads')
                    # return redirect('search')
                return redirect('leadedit', id)
                    # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                
            elif 'careerdesssapi' in request.POST:
                # Call second API
                # try:
                #     api_url = 'https://career.desss.com/dynamic/careerdesssapi.php'
                #     api_params = {
                #         'action': 'lead',
                #         'phone': my_model.year,
                #         'message': my_model.filmurl,
                #         'date': my_model.title,
                #     }
                #     response = requests.get(api_url, params=api_params)
                #     print(response.text)  # Print the response from the API
                #     return redirect('leads')
                # except:
                #     return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                id = my_model.id
                if id==id:
                    year = my_model.year
                    filmurl = my_model.filmurl
                    # replacements = [('%', ''), ('&', 'and')]

                    # for char, replacement in replacements:
                    #     if char in filmurl:
                    #         originaldata = filmurl.replace(char, replacement)

                    # print(originaldata)
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', filmurl)
                    
                    title = my_model.title
                    url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=lead&phone={year}&message={originaldata}&date={title}"
                    # api_params = {
                    #     'action': 'lead',
                    #     'phone': my_model.year,
                    #     'message': my_model.filmurl,
                    #     'date': my_model.title,
                    # }
                    # response = requests.get(api_url, params=api_params)
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API
                    # return render(request, 'confirmation.html')
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                    return redirect('leads')
                    # return redirect('search')
                return redirect('leadedit', id)
    else:
        form = FilmForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])

def sampleleadupdate(request,id):
    my_model = get_object_or_404(Emailsample, id=id)
    if request.method == 'POST':
        form = EmailsampleForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            # delete_idd=request.POST.get('id')
            if 'save_home' in request.POST:
                return redirect('emailnewleads')
            elif 'save_next' in request.POST:
                try:
                    next_model = Emailsample.objects.filter(id__gt=id).order_by('id')[0]
                    return redirect('emailnewleadsedit', id=next_model.id)
                    # return redirect('leads')
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'save_convert' in request.POST:
                status = Emailsample.objects.get(id=id)
                print(status)
                status.samplecheckstatus^= 1
                status.save()
                try:
                    next_model = Emailsample.objects.filter(id__gt=id).filter(samplecheckstatus=1).order_by('id')[0]
                    return redirect('emailnewleadsedit', id=next_model.id)
                
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                try:
                    next_model = Emailsample.objects.filter(id__gt=id).filter(samplecheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Emailsample, id=id)
                    id=next_model.id
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('emailnewleadsedit', id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                try:
                    # next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    next_model = Emailsample.objects.filter(id__gt=id).filter(samplecheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Emailsample, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('emailnewleadsedit', id)
                except IndexError:
                    obj = get_object_or_404(Emailsample, id=id)
                    obj.delete()
                    return render(request, 'navigation.html')
            elif 'chiliadstaffingapi' in request.POST:
                id = my_model.id
                if id==id:
                    firstname = my_model.firstname
                    lastname = my_model.lastname
                    email = my_model.email
                    username = my_model.username
                    password = my_model.password
                    company = my_model.company
                    phonenumber = my_model.phonenumber
                    address = my_model.address
                    address2 = my_model.address2
                    city = my_model.city
                    state = my_model.state
                    zipcode = my_model.zipcode
                    occupation = my_model.occupation
                    description = my_model.description
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', description)
                    
                    # title = my_model.title
                    url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                    # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API
                    status = Emailsample.objects.get(id=id)
                    print(status)
                    status.samplecheckstatus^= 1
                    status.save()
                    return redirect('emailnewleads')
                    # return redirect('search')
                return redirect('emailnewleadsedit', id)

                
            elif 'careerdesssapi' in request.POST:
                id = my_model.id
                if id==id:
                    firstname = my_model.firstname
                    lastname = my_model.lastname
                    email = my_model.email
                    username = my_model.username
                    password = my_model.password
                    company = my_model.company
                    phonenumber = my_model.phonenumber
                    address = my_model.address
                    address2 = my_model.address2
                    city = my_model.city
                    state = my_model.state
                    zipcode = my_model.zipcode
                    occupation = my_model.occupation
                    description = my_model.description
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', description)
                    
                    # title = my_model.title
                    url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=employer_lead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                    # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API

                    status = Emailsample.objects.get(id=id)
                    print(status)
                    status.samplecheckstatus^= 1
                    status.save()
                    return redirect('emailnewleads')
                    # return redirect('search')
                return redirect('emailnewleadsedit', id)
    else:
        form = EmailsampleForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])




def customemailleadsupdate(request,id):
    my_model = get_object_or_404(Customemailleads, id=id)
    if request.method == 'POST':
        form = CustomemailleadsForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            # delete_idd=request.POST.get('id')
            if 'save_home' in request.POST:
                return redirect('customemailleads')
            elif 'save_next' in request.POST:
                try:
                    next_model = Customemailleads.objects.filter(id__gt=id).order_by('id')[0]
                    return redirect('customemailleadsview', id=next_model.id)
                    # return redirect('leads')
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'save_convert' in request.POST:
                status = Customemailleads.objects.get(id=id)
                print(status)
                status.bcheckstatus^= 1
                status.save()
                try:
                    next_model = Customemailleads.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    return redirect('customemailleadsview', id=next_model.id)
                
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                try:
                    next_model = Customemailleads.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Customemailleads, id=id)
                    id=next_model.id
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('customemailleadsview', id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                try:
                    # next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    next_model = Customemailleads.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Customemailleads, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('customemailleadsview', id)
                except IndexError:
                    obj = get_object_or_404(Customemailleads, id=id)
                    obj.delete()
                    return render(request, 'navigation.html')
            elif 'chiliadstaffingapi' in request.POST:
                id = my_model.id
                if id==id:
                    firstname = my_model.First_Name
                    lastname = my_model.Last_Name
                    experience = my_model.Experience
                    currentlocation = my_model.Current_Location
                    technology = my_model.Technology
                    relocation = my_model.Relocation
                    visa = my_model.Visa
                    noticeperiod = my_model.Notice_Period
                    benchsalesfirstname = my_model.Benchsales_First_Name
                    benchsaleslastname = my_model.Benchsales_Last_Name
                    benchsalescompany = my_model.Benchsales_Company
                    benchsalesemail = my_model.Benchsales_Email
                    benchsalesmobile = my_model.Benchsales_Mobile
                    benchsalesaddress = my_model.Benchsales_Address
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', benchsalesaddress)
                    
                    # title = my_model.title
                    url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=benchsales_lead&firstname={firstname}&lastname={lastname}&experience={experience}&currentlocation={currentlocation}&technology={technology}&relocation={relocation}&visa={visa}&noticeperiod={noticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"
                    # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API
                    status = Emailbenchsales.objects.get(id=id)
                    print(status)
                    status.bcheckstatus^= 1
                    status.save()
                    return redirect('customemailleads')
                    # return redirect('search')
                return redirect('customemailleadsview', id)

                
            elif 'careerdesssapi' in request.POST:
                id = my_model.id
                if id==id:
                    firstname = my_model.First_Name
                    lastname = my_model.Last_Name
                    experience = my_model.Experience
                    currentlocation = my_model.Current_Location
                    technology = my_model.Technology
                    relocation = my_model.Relocation
                    visa = my_model.Visa
                    noticeperiod = my_model.Notice_Period
                    benchsalesfirstname = my_model.Benchsales_First_Name
                    benchsaleslastname = my_model.Benchsales_Last_Name
                    benchsalescompany = my_model.Benchsales_Company
                    benchsalesemail = my_model.Benchsales_Email
                    benchsalesmobile = my_model.Benchsales_Mobile
                    benchsalesaddress = my_model.Benchsales_Address
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', benchsalesaddress)
                    
                    # title = my_model.title
                    url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={firstname}&lastname={lastname}&experience={experience}&currentlocation={currentlocation}&technology={technology}&relocation={relocation}&visa={visa}&noticeperiod={noticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"
                    # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API

                    status = Emailbenchsales.objects.get(id=id)
                    print(status)
                    status.bcheckstatus^= 1
                    status.save()
                    return redirect('customemailleads')
                    # return redirect('search')
                return redirect('customemailleadsview', id)
           
    else:
        form = EmailbenchsalesForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])



def customemailleadsupdateadd(request,id):
    my_model = get_object_or_404(Customleads, id=id)
    if request.method == 'POST':
        form = CustomleadsForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            # delete_idd=request.POST.get('id')
            if 'save_home' in request.POST:
                return redirect('customemailleads')
            elif 'save_next' in request.POST:
                try:
                    next_model = Customleads.objects.filter(id__gt=id).order_by('id')[0]
                    return redirect('customemailleadsedits', id=next_model.id)
                    # return redirect('leads')
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'save_convert' in request.POST:
                status = Customleads.objects.get(id=id)
                print(status)
                status.bcheckstatus^= 1
                status.save()
                try:
                    next_model = Customleads.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    return redirect('customemailleadsedits', id=next_model.id)
                
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                try:
                    next_model = Customleads.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Customleads, id=id)
                    id=next_model.id
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('customemailleadsedits', id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                try:
                    # next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    next_model = Customleads.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Customleads, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('customemailleadsedits', id)
                except IndexError:
                    obj = get_object_or_404(Customleads, id=id)
                    obj.delete()
                    return render(request, 'navigation.html')
           
            elif 'chiliadstaffingapi' in request.POST:
                id = my_model.id
                if id==id:
                    leadfirstname=my_model.leadfirstname
                    leadlastname=my_model.leadlastname
                    leademail=my_model.leademail
                    leadusername=my_model.leadusername
                    leadpassword='Desss@123'
                    leadcompany=my_model.leadcompany
                    leadphonenumber=my_model.leadphonenumber
                    leadaddress=my_model.leadaddress
                    leadaddress2=my_model.leadaddress2
                    leadcity=my_model.leadcity
                    leadstate=my_model.leadstate
                    leadzipcode=my_model.leadzipcode
                    # leadoccupation=request.POST['leadoccupation']
                    # leaddescription=request.POST['leaddescription']
                    # obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadoccupation=leadoccupation,leaddescription=leaddescription)
                    leadposition=my_model.leadposition
                    leaddescription=my_model.leaddescription
                    leadlocation = my_model.leadlocation
                    leadduration = my_model.leadduration
                    leadlegalstatus = my_model.leadlegalstatus
                    leadinterviewtype = my_model.leadinterviewtype
                    leadworktype = my_model.leadworktype
                    leadremote = my_model.leadremote
                    leadexperience = my_model.leadexperience
                    leadrate = my_model.leadrate
                     # Removing <br> tags from the description
                    # cleaned_leaddescription = leaddescription.replace("<br><br />", "")
                    cleaned_leaddescription = remove_br_tags_and_spaces(leaddescription)
                    # print(cleaned_leaddescription)
                    unwanted = "[%, <br>, <br />]"
                    originaldata = re.sub(unwanted, '', cleaned_leaddescription)
                    print(originaldata)
                    obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadposition=leadposition,leaddescription=originaldata,
                    leadlocation = leadlocation,leadduration = leadduration, leadlegalstatus = leadlegalstatus,leadinterviewtype = leadinterviewtype,leadworktype = leadworktype,leadremote = leadremote,
                    leadexperience = leadexperience,leadrate = leadrate)
                    obj.save()
                    # unwanted = "[%]"
                    # originaldata = re.sub(unwanted, '', leaddescription)
                                    
                    # title = my_model.title
                    # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}"
                    url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&id={id}&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={cleaned_leaddescription}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
                    # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API
                                    
                    if response.status_code == 200:
                        # status = Custombenchsales.objects.get(id=id)
                        # status = get_object_or_404(Customleads, id=id)
                        status = Customemailleads.objects.get(id=id)
                        print(status)
                        status.checkstatus^= 1
                        status.save()
                    #     # return redirect('customemailleads')
                    #     return render(request, 'customemaillead.html', messages)
                    # else:
                    #     # return redirect('customemailleads')
                    #      return render(request, 'customemaillead.html', messages)
                        messages.success(request, 'Your lead has been updated to chiliadstaffing.com successfully!')  # Success message
                        # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                        # return render(request, 'customemailleadsedits.html')
                        return redirect('customemailleadsedits', id)
                        # return render(request, 'customemaillead.html')
                        # return redirect('customemailleadsedits', id)
                    else:
                        messages.error(request, 'No update was made. In our database, the data you provided has already been updated!')  # Error message
                        # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                        # return render(request, 'customemailleadsedits.html')
                        return redirect('customemailleadsedits', id)
                        # return render(request, 'customemaillead.html')
                        # return redirect('customemailleadsedits', id)
                # return redirect('customemailleadsedits', id)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                # return redirect('customemailleads')
                                # return redirect('search')
                # return redirect('customemailleads')

                            
            elif 'careerdesssapi' in request.POST:
                    id = my_model.id
                    if id==id:
                        #leadid = my_model.id
                        leadfirstname=my_model.leadfirstname
                        leadlastname=my_model.leadlastname
                        leademail=my_model.leademail
                        leadusername=my_model.leadusername
                        leadpassword='Desss@123'
                        leadcompany=my_model.leadcompany
                        leadphonenumber=my_model.leadphonenumber
                        leadaddress=my_model.leadaddress
                        leadaddress2=my_model.leadaddress2
                        leadcity=my_model.leadcity
                        leadstate=my_model.leadstate
                        leadzipcode=my_model.leadzipcode
                        # leadoccupation=request.POST['leadoccupation']
                        # leaddescription=request.POST['leaddescription']
                        # obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadoccupation=leadoccupation,leaddescription=leaddescription)
                        leadposition=my_model.leadposition
                        leaddescription=my_model.leaddescription
                        leadlocation = my_model.leadlocation
                        leadduration = my_model.leadduration
                        leadlegalstatus = my_model.leadlegalstatus
                        leadinterviewtype = my_model.leadinterviewtype
                        leadworktype = my_model.leadworktype
                        leadremote = my_model.leadremote
                        leadexperience = my_model.leadexperience
                        leadrate = my_model.leadrate
                        # Removing <br> tags from the description
                        # cleaned_leaddescription = leaddescription.replace("<br><br />", "")
                        cleaned_leaddescription = remove_br_tags_and_spaces(leaddescription)
                        print(cleaned_leaddescription)
                        obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadposition=leadposition,leaddescription=cleaned_leaddescription,
                        leadlocation = leadlocation,leadduration = leadduration, leadlegalstatus = leadlegalstatus,leadinterviewtype = leadinterviewtype,leadworktype = leadworktype,leadremote = leadremote,
                        leadexperience = leadexperience,leadrate = leadrate)
                        obj.save()
                            # originaldata = re.sub(unwanted, '', benchsalesaddress)
                                        
                                        # title = my_model.title
                        # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}"
                        url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=employer_lead&id={id}&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={cleaned_leaddescription}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
                
                                        # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                        response = requests.get(url)
                        print(response.text)  # Print the response from the API

                           
                        # status = Customemailleads.objects.get(id=id)
                        # print(status)
                        # status.checkstatus^= 1
                        # status.save()
                        if response.status_code == 200:
                            status = Customemailleads.objects.get(id=id)
                            print(status)
                            status.checkstatus^= 1
                            status.save()
                            
                        #     # return redirect('customemailleads')
                        #     return render(request, 'customemaillead.html', messages)
                        # else:
                        #     # return redirect('customemailleads')
                        #      return render(request, 'customemaillead.html', messages)
                            messages.success(request, 'Your lead has been updated to career.desss.com successfully!')  # Success message
                            return redirect('customemailleadsedits', id)
                            # return render(request, 'customemailleadsedits.html')
                        else:
                            messages.error(request, 'No update was made. In our database, the data you provided has already been updated!')  # Error message
                            return redirect('customemailleadsedits', id)
                            # return render(request, 'customemailleadsedits.html')
            return redirect('customemailleadsedits', id)
                    #     return redirect('customemailleads')
                    # return redirect('customemailleadadd', id)
                        # return redirect('customemailleads')
    else:
        form = CustomleadsForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])
    # return redirect('customemailleads') 


def custombenchsalesupdateadd(request,id):
    my_model = get_object_or_404(Custombench, id=id)
    # if request.method == 'GET':
    #     objects=Custombenchsales.objects.get(id=id)

    #     content = objects.bsEmail_Bodyhtml

    #     html_content = content

    #     soup = BeautifulSoup(html_content, 'html.parser')
    #     table = soup.find('table')  # You may need to modify this to match the specific table you want to extract

    #     if table:
    #         data = []

    #         for row in table.find_all('tr'):
    #             cols = row.find_all('td')
    #             cols = [extract_data(col) for col in cols]
    #             data.append(cols)

    #         df = pd.DataFrame(data)
    #         # csv_filename = f'table_data_{idx}.csv'  # Generate a unique CSV file name for each row
    #         # df.to_csv(csv_filename, index=False)

    #         csv_filename = dot +str('table_data.csv')
    #         df.to_csv(csv_filename, index=False,)
    #         # df = pd.read_csv (csv_filename,  encoding='utf8',  header=0,  dtype=str, error_bad_lines=False, )
    #         df = pd.read_csv (csv_filename,  encoding='utf8',  header=0,  dtype=str,  )
    #         json_filename = dot+str('table_data.json')
    #         df.to_json (json_filename,)
    #         json_records = df.reset_index().to_json(orient ='records')
    #         data = []
    #         data = json.loads(json_records)
    #         context = {'d': data}
    #         return render(request, 'custombenchsalesedits.html', context)
    #     else:
    #         print("Table not found in the HTML content of row", id)
    #         object_bench=Custombench.objects.get(id=id)
    #         return render(request, 'custombenchsalesedits.html', {'object':object_bench,})
   


    if request.method == 'POST':
        form = CustombenchForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            # delete_idd=request.POST.get('id')
            if 'save_home' in request.POST:
                return redirect('custombenchsales')
            elif 'save_next' in request.POST:
                try:
                    next_model = Custombench.objects.filter(id__gt=id).order_by('id')[0]
                    return redirect('custombenchsalesedits', id=next_model.id)
                    # return redirect('leads')
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'save_convert' in request.POST:
                status = Custombench.objects.get(id=id)
                print(status)
                status.bcheckstatus^= 1
                status.save()
                try:
                    next_model = Custombench.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    return redirect('custombenchsalesedits', id=next_model.id)
                
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                try:
                    next_model = Custombench.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Custombench, id=id)
                    id=next_model.id
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('custombenchsalesedits', id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                try:
                    # next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    next_model = Custombench.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Custombench, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('custombenchsalesedits', id)
                except IndexError:
                    obj = get_object_or_404(Custombench, id=id)
                    obj.delete()
                    return render(request, 'navigation.html')
           
            elif 'chiliadstaffingapi' in request.POST:
                id = my_model.id
                if id==id:
                    benchfirstname=my_model.benchfirstname
                    benchlastname=my_model.benchlastname
                    benchexperience=my_model.benchexperience
                    Rate=my_model.Rate
                    Position=my_model.Position
                    Location=my_model.Location
                    Duration=my_model.Duration
                    benchrelocation=my_model.benchrelocation
                    Legal_Status=my_model.Legal_Status
                    benchnoticeperiod=my_model.benchnoticeperiod
                    benchsalesfirstname=my_model.benchsalesfirstname
                    benchsaleslastname=my_model.benchsaleslastname
                    benchsalescompany=my_model.benchsalescompany
                    benchsalesemail=my_model.benchsalesemail
                    benchsalesmobile = my_model.benchsalesmobile
                    benchsalesaddress = my_model.benchsalesaddress
                    Interview_Type = my_model.Interview_Type
                    Work_Type = my_model.Work_Type
                    Remote = my_model.Remote
            
                    # cleaned_leaddescription = remove_br_tags_and_spaces(leaddescription)
                    # print(cleaned_leaddescription)
                    # unwanted = "[%, <br>, <br />]"
                    # originaldata = re.sub(unwanted, '', cleaned_leaddescription)
                    # print(originaldata)
                    obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,
                    benchsalesmobile = benchsalesmobile,benchsalesaddress = benchsalesaddress, Interview_Type = Interview_Type,Work_Type = Work_Type,Remote = Remote)
                    obj.save()
                    # unwanted = "[%]"
                    # originaldata = re.sub(unwanted, '', leaddescription)
                                    
                    
                    url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&Rate={Rate}&Position={Position}&Location={Location}&Duration={Duration}&relocation={benchrelocation}&Legal_Status={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}"
    
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API
                                    
                    if response.status_code == 200:
                        # status = Custombenchsales.objects.get(id=id)
                        # # status = get_object_or_404(Customleads, id=id)
                        # print(status)
                        # status.bscheckstatus^= 1
                        # status.save()
                    #     # return redirect('customemailleads')
                    #     return render(request, 'customemaillead.html', messages)
                    # else:
                    #     # return redirect('customemailleads')
                    #      return render(request, 'customemaillead.html', messages)
                        messages.success(request, 'Your lead has been updated to chiliadstaffing.com successfully!')  # Success message
                        # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                        # return render(request, 'customemailleadsedits.html')
                        return redirect('custombenchsalesedits', id)
                        # return render(request, 'customemaillead.html')
                        # return redirect('customemailleadsedits', id)
                    else:
                        messages.error(request, 'No update was made. In our database, the data you provided has already been updated!')  # Error message
                        # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                        # return render(request, 'customemailleadsedits.html')
                        return redirect('custombenchsalesedits', id)
                        # return render(request, 'customemaillead.html')
                        # return redirect('customemailleadsedits', id)
                # return redirect('customemailleadsedits', id)
                # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                # return redirect('customemailleads')
                                # return redirect('search')
                # return redirect('customemailleads')

                            
            elif 'careerdesssapi' in request.POST:
                id = my_model.id
                if id==id:
                    benchfirstname=my_model.benchfirstname
                    benchlastname=my_model.benchlastname
                    benchexperience=my_model.benchexperience
                    Rate=my_model.Rate
                    Position=my_model.Position
                    Location=my_model.Location
                    Duration=my_model.Duration
                    benchrelocation=my_model.benchrelocation
                    Legal_Status=my_model.Legal_Status
                    benchnoticeperiod=my_model.benchnoticeperiod
                    benchsalesfirstname=my_model.benchsalesfirstname
                    benchsaleslastname=my_model.benchsaleslastname
                    benchsalescompany=my_model.benchsalescompany
                    benchsalesemail=my_model.benchsalesemail
                    benchsalesmobile = my_model.benchsalesmobile
                    benchsalesaddress = my_model.benchsalesaddress
                    Interview_Type = my_model.Interview_Type
                    Work_Type = my_model.Work_Type
                    Remote = my_model.Remote
            
                    # cleaned_leaddescription = remove_br_tags_and_spaces(leaddescription)
                    # print(cleaned_leaddescription)
                    # unwanted = "[%, <br>, <br />]"
                    # originaldata = re.sub(unwanted, '', cleaned_leaddescription)
                    # print(originaldata)
                    obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,
                    benchsalesmobile = benchsalesmobile,benchsalesaddress = benchsalesaddress, Interview_Type = Interview_Type,Work_Type = Work_Type,Remote = Remote)
                    obj.save()
                            # originaldata = re.sub(unwanted, '', benchsalesaddress)
                                        
                                        # title = my_model.title
            
                    url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&Rate={Rate}&Position={Position}&Location={Location}&Duration={Duration}&relocation={benchrelocation}&Legal_Status={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}"
                
                                       
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API

                           
                        # status = Customemailleads.objects.get(id=id)
                        # print(status)
                        # status.checkstatus^= 1
                        # status.save()
                    if response.status_code == 200:
                        # status = Custombenchsales.objects.get(id=id)
                        # print(status)
                        # status.bscheckstatus^= 1
                        # status.save()
                            
                        #     # return redirect('customemailleads')
                        #     return render(request, 'customemaillead.html', messages)
                        # else:
                        #     # return redirect('customemailleads')
                        #      return render(request, 'customemaillead.html', messages)
                        messages.success(request, 'Your lead has been updated to career.desss.com successfully!')  # Success message
                        return redirect('custombenchsalesedits', id)
                            # return render(request, 'customemailleadsedits.html')
                    else:
                        messages.error(request, 'No update was made. In our database, the data you provided has already been updated!')  # Error message
                        return redirect('custombenchsalesedits', id)
                            # return render(request, 'customemailleadsedits.html')
            return redirect('custombenchsalesedits', id)
                    #     return redirect('customemailleads')
                    # return redirect('customemailleadadd', id)
                        # return redirect('customemailleads')
    else:
        form = CustombenchForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])
    # return redirect('customemailleads') 

def custombenchsalesupdate(request,id):
    my_model = get_object_or_404(Custombenchsales, id=id)
    if request.method == 'POST':
        form = CustombenchsalesForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            # delete_idd=request.POST.get('id')
            if 'save_home' in request.POST:
                return redirect('custombenchsales')
            elif 'save_next' in request.POST:
                try:
                    next_model = Custombenchsales.objects.filter(id__gt=id).order_by('id')[0]
                    return redirect('custombenchsalesview', id=next_model.id)
                    # return redirect('leads')
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'save_convert' in request.POST:
                status = Custombenchsales.objects.get(id=id)
                print(status)
                status.bcheckstatus^= 1
                status.save()
                try:
                    next_model = Custombenchsales.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    return redirect('custombenchsalesview', id=next_model.id)
                
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                try:
                    next_model = Custombenchsales.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Custombenchsales, id=id)
                    id=next_model.id
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('custombenchsalesview', id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                try:
                    # next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    next_model = Custombenchsales.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Custombenchsales, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('custombenchsalesview', id)
                except IndexError:
                    obj = get_object_or_404(Custombenchsales, id=id)
                    obj.delete()
                    return render(request, 'navigation.html')
           
    else:
        form = CustombenchsalesForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])

def benchsalesupdate(request,id):
    my_model = get_object_or_404(Emailbenchsales, id=id)
    if request.method == 'POST':
        form = EmailbenchsalesForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            # delete_idd=request.POST.get('id')
            if 'save_home' in request.POST:
                return redirect('benchsales')
            elif 'save_next' in request.POST:
                try:
                    next_model = Emailbenchsales.objects.filter(id__gt=id).order_by('id')[0]
                    return redirect('emailbenchsalesedit', id=next_model.id)
                    # return redirect('leads')
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'save_convert' in request.POST:
                status = Emailbenchsales.objects.get(id=id)
                print(status)
                status.bcheckstatus^= 1
                status.save()
                try:
                    next_model = Emailbenchsales.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    return redirect('emailbenchsalesedit', id=next_model.id)
                
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                try:
                    next_model = Emailbenchsales.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Emailbenchsales, id=id)
                    id=next_model.id
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('emailbenchsalesedit', id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                try:
                    # next_model = Film.objects.filter(id__gt=id).exclude(dropdownlist='New').filter(checkstatus=1).order_by('id')[0]
                    next_model = Emailbenchsales.objects.filter(id__gt=id).filter(bcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Emailbenchsales, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('emailbenchsalesedit', id)
                except IndexError:
                    obj = get_object_or_404(Emailbenchsales, id=id)
                    obj.delete()
                    return render(request, 'navigation.html')
            elif 'chiliadstaffingapi' in request.POST:
                id = my_model.id
                if id==id:
                    firstname = my_model.First_Name
                    lastname = my_model.Last_Name
                    experience = my_model.Experience
                    currentlocation = my_model.Current_Location
                    technology = my_model.Technology
                    relocation = my_model.Relocation
                    visa = my_model.Visa
                    noticeperiod = my_model.Notice_Period
                    benchsalesfirstname = my_model.Benchsales_First_Name
                    benchsaleslastname = my_model.Benchsales_Last_Name
                    benchsalescompany = my_model.Benchsales_Company
                    benchsalesemail = my_model.Benchsales_Email
                    benchsalesmobile = my_model.Benchsales_Mobile
                    benchsalesaddress = my_model.Benchsales_Address
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', benchsalesaddress)
                    
                    # title = my_model.title
                    url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=benchsales_lead&firstname={firstname}&lastname={lastname}&experience={experience}&currentlocation={currentlocation}&technology={technology}&relocation={relocation}&visa={visa}&noticeperiod={noticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"
                    # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API
                    status = Emailbenchsales.objects.get(id=id)
                    print(status)
                    status.bcheckstatus^= 1
                    status.save()
                    return redirect('benchsales')
                    # return redirect('search')
                return redirect('emailbenchsalesedit', id)

                
            elif 'careerdesssapi' in request.POST:
                id = my_model.id
                if id==id:
                    firstname = my_model.First_Name
                    lastname = my_model.Last_Name
                    experience = my_model.Experience
                    currentlocation = my_model.Current_Location
                    technology = my_model.Technology
                    relocation = my_model.Relocation
                    visa = my_model.Visa
                    noticeperiod = my_model.Notice_Period
                    benchsalesfirstname = my_model.Benchsales_First_Name
                    benchsaleslastname = my_model.Benchsales_Last_Name
                    benchsalescompany = my_model.Benchsales_Company
                    benchsalesemail = my_model.Benchsales_Email
                    benchsalesmobile = my_model.Benchsales_Mobile
                    benchsalesaddress = my_model.Benchsales_Address
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', benchsalesaddress)
                    
                    # title = my_model.title
                    url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={firstname}&lastname={lastname}&experience={experience}&currentlocation={currentlocation}&technology={technology}&relocation={relocation}&visa={visa}&noticeperiod={noticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"
                    # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API

                    status = Emailbenchsales.objects.get(id=id)
                    print(status)
                    status.bcheckstatus^= 1
                    status.save()
                    return redirect('benchsales')
                    # return redirect('search')
                return redirect('emailbenchsalesedit', id)
    else:
        form = EmailbenchsalesForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])


# def emailleadupdate(request,id):
#     my_model = get_object_or_404(Emaillead, id=id)
#     if request.method == 'POST':
#         form = EmailleadForm(request.POST, instance=my_model)
#         if form.is_valid():
#             form.save()
#             # delete_idd=request.POST.get('id')
#             if 'save_home' in request.POST:
#                 return redirect('emailhome')
#             elif 'save_next' in request.POST:
#                 try:
#                     next_model = Emaillead.objects.filter(id__gt=id).exclude(emaildropdownlist='New').order_by('id')[0]
#                     return redirect('emailleadedit', id=next_model.id)
#                 except IndexError:
#                     return render(request, 'navigation.html')
#             elif 'save_continue' in request.POST:
#                 return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
#             elif 'save_convert' in request.POST:
#                 status = Emaillead.objects.get(id=id)
#                 print(status)
#                 status.emailcheckstatus^= 1
#                 status.save()
#                 try:
#                     next_model = Emaillead.objects.filter(id__gt=id).exclude(emaildropdownlist='New').filter(emailcheckstatus=1).order_by('id')[0]
#                     return redirect('emailleadedit', id=next_model.id)
#                 except IndexError:
#                     return render(request, 'navigation.html')
#             elif 'delete_d' in request.POST:
#                 # snippet_ids=request.POST.getlist('ids[]')
#                 print(id)
#                 try:
#                     next_model = Emaillead.objects.filter(id__gt=id).exclude(emaildropdownlist='New').filter(emailcheckstatus=1).order_by('id')[0]
#                     obj = get_object_or_404(Emaillead, id=id)
#                     id=next_model.id
#                     # obj = get_object_or_404(Film, id=id)
#                     obj.delete()
#                     return redirect('emailleadedit', id)
#                 except IndexError:
#                     return render(request, 'navigation.html')
#             elif 'delete_dynamic' in request.POST:
#                 try:
#                     # next_model = Emaillead.objects.filter(id__gt=id).exclude(emaildropdownlist='New').filter(emailcheckstatus=1).order_by('id')[0]
#                     next_model = Emaillead.objects.filter(id__gt=id).filter(emailcheckstatus=1).order_by('id')[0]
#                     obj = get_object_or_404(Emaillead, id=id)
#                     id = next_model.id
#                     obj.delete()
#                     return redirect('emailleadedit', id)
#                 except IndexError:
#                     obj = get_object_or_404(Emaillead, id=id)
#                     obj.delete()
#                     return render(request, 'navigation.html')
#             elif 'chiliadstaffingapi' in request.POST:
#                 # Call first A
#                 id = my_model.id
#                 if id==id:
#                     year = my_model.year
#                     filmurl = my_model.filmurl
#                     # replacements = [('%', ''), ('&', 'and'), ('∷', '')]

#                     # for char, replacement in replacements:
#                     #     if char in filmurl:
#                     #         filmurl = filmurl.replace(char, replacement)

#                     # print(filmurl)
#                     # originaldata = re.sub(r'\W+', '', filmurl)
#                     # print(originaldata)
#                     unwanted = "[%]"
#                     originaldata = re.sub(unwanted, '', filmurl)
                    
#                     title = my_model.title
#                     url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=lead&phone={year}&message={originaldata}&date={title}"
#                     # api_params = {
#                     #     'action': 'lead',
#                     #     'phone': my_model.year,
#                     #     'message': my_model.filmurl,
#                     #     'date': my_model.title,
#                     # }
#                     # response = requests.get(api_url, params=api_params)
#                     response = requests.get(url)
#                     print(response.text)  # Print the response from the API
#                     status = Emaillead.objects.get(id=id)
#                     print(status)
#                     status.emailcheckstatus^= 1
#                     status.save()
#                     # return redirect('leads')
#                     return redirect('search')
#                 return redirect('emailleadedit', id)
#                     # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                
#             elif 'careerdesssapi' in request.POST:
#                 # Call second API
#                 # try:
#                 #     api_url = 'https://career.desss.com/dynamic/careerdesssapi.php'
#                 #     api_params = {
#                 #         'action': 'lead',
#                 #         'phone': my_model.year,
#                 #         'message': my_model.filmurl,
#                 #         'date': my_model.title,
#                 #     }
#                 #     response = requests.get(api_url, params=api_params)
#                 #     print(response.text)  # Print the response from the API
#                 #     return redirect('leads')
#                 # except:
#                 #     return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
#                 id = my_model.id
#                 if id==id:
#                     year = my_model.year
#                     filmurl = my_model.filmurl
#                     # replacements = [('%', ''), ('&', 'and')]

#                     # for char, replacement in replacements:
#                     #     if char in filmurl:
#                     #         originaldata = filmurl.replace(char, replacement)

#                     # print(originaldata)
#                     unwanted = "[%]"
#                     originaldata = re.sub(unwanted, '', filmurl)
                    
#                     title = my_model.title
#                     url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=lead&phone={year}&message={originaldata}&date={title}"
#                     # api_params = {
#                     #     'action': 'lead',
#                     #     'phone': my_model.year,
#                     #     'message': my_model.filmurl,
#                     #     'date': my_model.title,
#                     # }
#                     # response = requests.get(api_url, params=api_params)
#                     response = requests.get(url)
#                     print(response.text)  # Print the response from the API
#                     # return render(request, 'confirmation.html')
#                     status = Emaillead.objects.get(id=id)
#                     print(status)
#                     status.emailcheckstatus^= 1
#                     status.save()
#                     # return redirect('leads')
#                     return redirect('search')
#                 return redirect('emailleadedit', id)
#     else:
#         form = EmailleadForm(instance=my_model)
#     return redirect(request.META['HTTP_REFERER'])

def emailleadoppupdate(request,id):
    my_model = get_object_or_404(Emailleadoppurtunities, id=id)
    if request.method == 'POST':
        form = EmailleadoppurtunitiesForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            # delete_idd=request.POST.get('id')
            if 'save_home' in request.POST:
                return redirect('emailleadoppurtunities')
            elif 'save_next' in request.POST:
                try:
                    next_model = Emailleadoppurtunities.objects.filter(id__gt=id).exclude(refdropdownlist='New').order_by('id')[0]
                    return redirect('emailleadoppurtunitiesedit', id=next_model.id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'save_convert' in request.POST:
                status = Emailleadoppurtunities.objects.get(id=id)
                print(status)
                status.refcheckstatus^= 1
                status.save()
                try:
                    next_model = Emailleadoppurtunities.objects.filter(id__gt=id).exclude(refdropdownlist='New').filter(refcheckstatus=1).order_by('id')[0]
                    return redirect('emailleadoppurtunitiesedit', id=next_model.id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                try:
                    next_model = Emailleadoppurtunities.objects.filter(id__gt=id).exclude(refdropdownlist='New').filter(refcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Emailleadoppurtunities, id=id)
                    id=next_model.id
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('emailleadoppurtunitiesedit', id)
                # except IndexError:
                except Exception as e:
                    print(e)
                    return render(request, 'navigation.html')
            # elif 'delete_dynamic' in request.POST:
            #     try:
            #         # next_model = Emailleadoppurtunities.objects.filter(id__gt=id).exclude(refdropdownlist='New').filter(refcheckstatus=1).order_by('id')[0]
            #         next_model = Emailleadoppurtunities.objects.filter(id__gt=id).filter(emailcheckstatus=1).order_by('id')[0]
            #         obj = get_object_or_404(Emailleadoppurtunities, id=id)
            #         id = next_model.id
            #         obj.delete()
            #         # print(id)
            #         return redirect('emailleadoppurtunitiesedit', id)
                
            #     except IndexError:
            #         obj = get_object_or_404(Emailleadoppurtunities, id=id)
            #         obj.delete()
            #         return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                try:
                    # next_model = Emaillead.objects.filter(id__gt=id).exclude(emaildropdownlist='New').filter(refcheckstatus=1).order_by('id')[0]
                    next_model = Emailleadoppurtunities.objects.filter(id__gt=id).filter(refcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Emailleadoppurtunities, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('emailleadoppurtunitiesedit', id)
                except IndexError:
                    obj = get_object_or_404(Emailleadoppurtunities, id=id)
                    obj.delete()
                    return render(request, 'navigation.html')
            elif 'chiliadstaffingapi' in request.POST:
                # Call first A
                id = my_model.id
                if id==id:
                    year = my_model.year
                    filmurl = my_model.filmurl
                    # replacements = [('%', ''), ('&', 'and'), ('∷', '')]

                    # for char, replacement in replacements:
                    #     if char in filmurl:
                    #         filmurl = filmurl.replace(char, replacement)

                    # print(filmurl)
                    # originaldata = re.sub(r'\W+', '', filmurl)
                    # print(originaldata)
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', filmurl)
                    
                    title = my_model.title
                    url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=lead&phone={year}&message={originaldata}&date={title}"
                    # api_params = {
                    #     'action': 'lead',
                    #     'phone': my_model.year,
                    #     'message': my_model.filmurl,
                    #     'date': my_model.title,
                    # }
                    # response = requests.get(api_url, params=api_params)
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API
                    status = Emailleadoppurtunities.objects.get(id=id)
                    print(status)
                    status.refcheckstatus^= 1
                    status.save()
                    # return redirect('leads')
                    return redirect('search')
                return redirect('emailleadoppurtunitiesedit', id)
                    # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                
            elif 'careerdesssapi' in request.POST:
                # Call second API
                # try:
                #     api_url = 'https://career.desss.com/dynamic/careerdesssapi.php'
                #     api_params = {
                #         'action': 'lead',
                #         'phone': my_model.year,
                #         'message': my_model.filmurl,
                #         'date': my_model.title,
                #     }
                #     response = requests.get(api_url, params=api_params)
                #     print(response.text)  # Print the response from the API
                #     return redirect('leads')
                # except:
                #     return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                id = my_model.id
                if id==id:
                    year = my_model.year
                    filmurl = my_model.filmurl
                    # replacements = [('%', ''), ('&', 'and')]

                    # for char, replacement in replacements:
                    #     if char in filmurl:
                    #         originaldata = filmurl.replace(char, replacement)

                    # print(originaldata)
                    unwanted = "[%]"
                    originaldata = re.sub(unwanted, '', filmurl)
                    
                    title = my_model.title
                    url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=lead&phone={year}&message={originaldata}&date={title}"
                    # api_params = {
                    #     'action': 'lead',
                    #     'phone': my_model.year,
                    #     'message': my_model.filmurl,
                    #     'date': my_model.title,
                    # }
                    # response = requests.get(api_url, params=api_params)
                    response = requests.get(url)
                    print(response.text)  # Print the response from the API
                    # return render(request, 'confirmation.html')
                    status = Emailleadoppurtunities.objects.get(id=id)
                    print(status)
                    status.refcheckstatus^= 1
                    status.save()
                    # return redirect('leads')
                    return redirect('search')
                return redirect('emailleadoppurtunitiesedit', id)
    else:
        form = EmailleadoppurtunitiesForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])
# def searchview(request):
#     if 'search' in request.GET:
#         search_term = request.GET['search']
#         search_result = whatsapp.objects.all().filter(chat__icontains=search_term)
#         return render(request, 'overview.html', {'articles' : articles, 'search_result': search_result })  
#     search_result = "Not Found"
#     articles = whatsapp.objects.all()
#     return render(request, 'overview.html', {'articles' : articles, 'search_result': search_result })    


#search box for django
def search(request):
    location_list = LocationChoiceField()
    label_list = LabelChoiceField()
    if 'q' in request.GET:
        q = request.GET['q']
        # data = Film.objects.filter(filmurl__icontains=q)
        multiple_q = Q(Q(year__icontains=q) | Q(filmurl__icontains=q))
        details = Film.objects.filter(multiple_q).filter(Q(checkstatus=0))
        # object=Film.objects.get(id=id)
    elif request.GET.get('locations'):
        selected_location = request.GET.get('locations')
        details = Film.objects.filter(checkstatus=selected_location)
    elif request.GET.get('label'):
        labels = request.GET.get('label')
        details = Film.objects.filter(dropdownlist=labels)
    else:
        details = Film.objects.all().order_by('-id')
    context = {
        'details': details,
        'location_list': location_list,
        'label_list': label_list
    }
    return render(request, 'search.html', context)

#check box delete
from django.views.generic import View
# from core import Film

class Product_view(View):
    

    def get(self,  request):
        # location_list = LocationChoiceField()
        label_list = LabelChoiceField()
        # datesdatalist = DateChoiceField()


        if 'q' in request.GET:
            q = request.GET['q']
            # data = Film.objects.filter(filmurl__icontains=q)
            multiple_q = Q(Q(year__icontains=q) | Q(filmurl__icontains=q))
            details = Film.objects.filter(multiple_q).filter(Q(dropdownlist='New'))
            # object=Film.objects.get(id=id)
        elif request.GET.get('locations'):
            selected_location = request.GET.get('locations')
            details = Film.objects.filter(checkstatus=selected_location)
        elif request.GET.get('label'):
            labels = request.GET.get('label')
            details = Film.objects.filter(dropdownlist=labels)#.filter(dropdownlist='New')
        elif request.GET.get('datesdata'):
            selected_datedata = request.GET.get('datesdata')
            details = Film.objects.filter(dropdownlist='New',title=selected_datedata)
        else:

            details = Film.objects.filter(dropdownlist='New').order_by('id')
        context = {
            'details': details,

            'label_list': label_list,

           
        }
        return render(request, 'retrieve.html', context)

    def post(self, request, *args, **kwargs):

         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')

            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:

                    obj = get_object_or_404(Film, id = id)
                    obj.delete()
                return redirect('home')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                return redirect('home')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(Film, id=id)
                obj.delete()
                
                return redirect('home')
            else:
                return redirect('home')

# class Emailproduct_view(View):
    

#     def get(self,  request):
#         # location_list = LocationChoiceField()
#         label_list = LabelChoiceField()
#         # datesdatalist = DateChoiceField()


#         if 'q' in request.GET:
#             q = request.GET['q']
#             # data = Film.objects.filter(filmurl__icontains=q)
#             multiple_q = Q(Q(usermob__icontains=q) | Q(userdetails__icontains=q))
#             details = Emaillead.objects.filter(multiple_q).filter(Q(emaildropdownlist='New'))
#             # object=Film.objects.get(id=id)
#         elif request.GET.get('locations'):
#             selected_location = request.GET.get('locations')
#             details = Emaillead.objects.filter(emailcheckstatus=selected_location)
#         elif request.GET.get('label'):
#             labels = request.GET.get('label')
#             print(labels)
#             details = Emaillead.objects.filter(emaildropdownlist=labels)#.filter(dropdownlist='New')
#         elif request.GET.get('datesdata'):
#             selected_datedata = request.GET.get('datesdata')
#             details = Emaillead.objects.filter(emaildropdownlist='New',title=selected_datedata)
#         else:

#             details = Emaillead.objects.filter(emaildropdownlist='New').order_by('id')
#         context = {
#             'details': details,

#             'label_list': label_list,

           
#         }
#         return render(request, 'emailretrieve.html', context)

#     def post(self, request, *args, **kwargs):

#          if request.method=="POST":
#             product_ids=request.POST.getlist('id[]')

#             snippet_ids=request.POST.getlist('ids[]')
#             delete_idd=request.POST.get('id')
#             print(product_ids)
#             print(snippet_ids)
#             if 'id[]' in request.POST:
#                 print(product_ids)
#                 for id in product_ids:

#                     obj = get_object_or_404(Emaillead, id = id)
#                     obj.delete()
#                 return redirect('emailhome')
#             elif 'ids[]' in request.POST:

#                 print(snippet_ids)
#                 for id in snippet_ids:
   
#                     print(id)
#                     status = Emaillead.objects.get(id=id)
#                     print(status)
#                     status.emailcheckstatus^= 1
#                     status.save()
#                 return redirect('emailhome')
#             elif 'id' in request.POST:

#                 print(delete_idd)
     
#                 id = delete_idd
#                 obj = get_object_or_404(Emaillead, id=id)
#                 obj.delete()
                
#                 return redirect('emailhome')
#             else:
#                 return redirect('emailhome')             

class Emailopp_view(View):
    

    def get(self,  request):
        # location_list = LocationChoiceField()
        label_list = LabelChoiceField()
        # datesdatalist = DateChoiceField()


        if 'q' in request.GET:
            q = request.GET['q']
            # data = Film.objects.filter(filmurl__icontains=q)
            multiple_q = Q(Q(refusermob__icontains=q) | Q(refuserdetails__icontains=q))
            details = Emailleadoppurtunities.objects.filter(multiple_q).filter(Q(refdropdownlist='New'))
            # object=Film.objects.get(id=id)
        elif request.GET.get('locations'):
            selected_location = request.GET.get('locations')
            details = Emailleadoppurtunities.objects.filter(refcheckstatus=selected_location)
        elif request.GET.get('label'):
            labels = request.GET.get('label')
            details = Emailleadoppurtunities.objects.filter(refdropdownlist=labels)#.filter(dropdownlist='New')
        elif request.GET.get('datesdata'):
            selected_datedata = request.GET.get('datesdata')
            details = Emailleadoppurtunities.objects.filter(refdropdownlist='New',title=selected_datedata)
        else:

            details = Emailleadoppurtunities.objects.filter(refdropdownlist='New').order_by('id')
        context = {
            'details': details,

            'label_list': label_list,

           
        }
        return render(request, 'emailleadopp.html', context)

    def post(self, request, *args, **kwargs):

         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')

            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:

                    obj = get_object_or_404(Emailleadoppurtunities, id = id)
                    obj.delete()
                return redirect('emailleadoppurtunities')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = Emailleadoppurtunities.objects.get(id=id)
                    print(status)
                    status.refcheckstatus^= 1
                    status.save()
                return redirect('emailleadoppurtunities')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(Emailleadoppurtunities, id=id)
                obj.delete()
                
                return redirect('emailleadoppurtunities')
            else:
                return redirect('emailleadoppurtunities')

class Emailsamplelead_view(View):
    

    def get(self,  request):
        # location_list = LocationChoiceField()
        label_list = LabelChoiceField()
        # datesdatalist = DateChoiceField()


        if 'q' in request.GET:
            q = request.GET['q']
            # data = Film.objects.filter(filmurl__icontains=q)
            multiple_q = Q(Q(firstname__icontains=q) | Q(lastname__icontains=q) | Q(email__icontains=q) | Q(username__icontains=q) | Q(company__icontains=q) | Q(phonenumber__icontains=q) | Q(address__icontains=q) | Q(address2__icontains=q) | Q(city__icontains=q) | Q(state__icontains=q) | Q(zipcode__icontains=q) | Q(occupation__icontains=q) | Q(description__icontains=q))
            details = Emailsample.objects.filter(multiple_q).filter(Q(sampledropdownlist='New'))
            # object=Film.objects.get(id=id)
        elif request.GET.get('locations'):
            selected_location = request.GET.get('locations')
            details = Emailsample.objects.filter(samplecheckstatus=selected_location)
        elif request.GET.get('label'):
            labels = request.GET.get('label')
            details = Emailsample.objects.filter(sampledropdownlist=labels)#.filter(dropdownlist='New')
        elif request.GET.get('datesdata'):
            selected_datedata = request.GET.get('datesdata')
            details = Emailsample.objects.filter(sampledropdownlist='New',title=selected_datedata)
        else:

            details = Emailsample.objects.filter(sampledropdownlist='New').order_by('id')
        context = {
            'details': details,

            'label_list': label_list,

           
        }
        return render(request, 'emailsample.html', context)

    def post(self, request, *args, **kwargs):

         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')

            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:

                    obj = get_object_or_404(Emailsample, id = id)
                    obj.delete()
                return redirect('emailnewleads')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = Emailsample.objects.get(id=id)
                    print(status)
                    status.samplecheckstatus^= 1
                    status.save()
                return redirect('emailnewleads')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(Emailsample, id=id)
                obj.delete()
                
                return redirect('emailnewleads')
            else:
                return redirect('emailnewleads')


class Leads_view(View):
    
    def get(self,  request):
        # location_list = LocationChoiceField()
        label_list = LabelChoiceField()

        if 'q' in request.GET:
            q = request.GET['q']
            # data = Film.objects.filter(filmurl__icontains=q)
            multiple_q = Q(Q(year__icontains=q) | Q(filmurl__icontains=q))
            details = Film.objects.filter(multiple_q).filter(~Q(dropdownlist='New'))
            # object=Film.objects.get(id=id)
        elif request.GET.get('locations'):
            selected_location = request.GET.get('locations')
            details = Film.objects.filter(checkstatus=selected_location)
        elif request.GET.get('label'):
            labels = request.GET.get('label')
            details = Film.objects.filter(dropdownlist=labels)
        else:
         
            details = Film.objects.exclude(dropdownlist='New').order_by('id')

        context = {
            'details': details,
            'label_list': label_list
        }
        return render(request, 'leadtype.html', context)
      

    def post(self, request, *args, **kwargs):
      
         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')
            # if product_ids == product_ids:
            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:
                    # product = Film.object.get(pk=id)
                    obj = get_object_or_404(Film, id = id)
                    obj.delete()
                return redirect('home')
            elif 'ids[]' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(snippet_ids)
                for id in snippet_ids:
             
                    print(id)
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                return redirect('leads')
            elif 'id' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(delete_idd)
              
                id = delete_idd
                obj = get_object_or_404(Film, id=id)
                obj.delete()
                
                return redirect('leads')
            else:
                return redirect('leads')


class Emailbenchsales_view(View):
    

    def get(self,  request):
        # location_list = LocationChoiceField()
        label_list = LabelChoiceField()
        # datesdatalist = DateChoiceField()


        if 'q' in request.GET:
            q = request.GET['q']
            # data = Film.objects.filter(filmurl__icontains=q)
            multiple_q = Q(Q(First_Name__icontains=q) | Q(Last_Name__icontains=q) | Q(Experience__icontains=q) | Q(Current_Location__icontains=q) | Q(Technology__icontains=q) | Q(Relocation__icontains=q) | Q(Visa__icontains=q) | Q(Notice_Period__icontains=q) | Q(Benchsales_First_Name__icontains=q) | Q(Benchsales_Last_Name__icontains=q) | Q(Benchsales_Company__icontains=q) | Q(Benchsales_Email__icontains=q) | Q(Benchsales_Mobile__icontains=q) | Q(Benchsales_Address__icontains=q) | Q(created_date__icontains=q))
            details = Emailbenchsales.objects.filter(multiple_q).filter(Q(bdropdownlist='Benchsales'))
            # object=Film.objects.get(id=id)
        elif request.GET.get('locations'):
            selected_location = request.GET.get('locations')
            details = Emailbenchsales.objects.filter(bcheckstatus=selected_location)
        elif request.GET.get('label'):
            labels = request.GET.get('label')
            details = Emailbenchsales.objects.filter(bdropdownlist=labels)#.filter(dropdownlist='New')
        elif request.GET.get('datesdata'):
            selected_datedata = request.GET.get('datesdata')
            details = Emailbenchsales.objects.filter(bdropdownlist='Benchsales',title=selected_datedata)
        else:

            details = Emailbenchsales.objects.filter(bdropdownlist='Benchsales').order_by('id')
        context = {
            'details': details,

            'label_list': label_list,

           
        }
        return render(request, 'emailbenchsales.html', context)

    def post(self, request, *args, **kwargs):

         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')

            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:

                    obj = get_object_or_404(Emailbenchsales, id = id)
                    obj.delete()
                return redirect('benchsales')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = Emailbenchsales.objects.get(id=id)
                    print(status)
                    status.bcheckstatus^= 1
                    status.save()
                return redirect('benchsales')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(Emailbenchsales, id=id)
                obj.delete()
                
                return redirect('benchsales')
            else:
                return redirect('benchsales')


class Leads_view(View):
    
    def get(self,  request):
        # location_list = LocationChoiceField()
        label_list = LabelChoiceField()

        if 'q' in request.GET:
            q = request.GET['q']
            # data = Film.objects.filter(filmurl__icontains=q)
            multiple_q = Q(Q(year__icontains=q) | Q(filmurl__icontains=q))
            details = Film.objects.filter(multiple_q).filter(~Q(dropdownlist='New'))
            # object=Film.objects.get(id=id)
        elif request.GET.get('locations'):
            selected_location = request.GET.get('locations')
            details = Film.objects.filter(checkstatus=selected_location)
        elif request.GET.get('label'):
            labels = request.GET.get('label')
            details = Film.objects.filter(dropdownlist=labels)
        else:
         
            details = Film.objects.exclude(dropdownlist='New').order_by('id')

        context = {
            'details': details,
            'label_list': label_list
        }
        return render(request, 'leadtype.html', context)
      

    def post(self, request, *args, **kwargs):
      
         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')
            # if product_ids == product_ids:
            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:
                    # product = Film.object.get(pk=id)
                    obj = get_object_or_404(Film, id = id)
                    obj.delete()
                return redirect('home')
            elif 'ids[]' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(snippet_ids)
                for id in snippet_ids:
             
                    print(id)
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                return redirect('leads')
            elif 'id' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(delete_idd)
              
                id = delete_idd
                obj = get_object_or_404(Film, id=id)
                obj.delete()
                
                return redirect('leads')
            else:
                return redirect('leads')
            


def status(request,id):

    status = Film.objects.get(id=id)
    print(status)
    status.checkstatus^= 1
    status.save()
    return redirect(request.META['HTTP_REFERER'])
    

from core.serializers import SnippetSerializer
class SnippetList(ListCreateAPIView):
    serializer_class = SnippetSerializer

    # def get_queryset(self):
    #     # Get URL parameter as a string, if exists 
    #     ids = self.request.query_params.get('ids', None)
    #     print(ids)
    #     # Get snippets for ids if they exist
    #     if ids is not None:
    #         # try:
    #         # Convert parameter string to list of integers
    #         ids = [ int(x) for x in ids.split(',') ]
    #         # Get objects for all parameter ids 
    #         # queryset = Film.objects.filter(pk__in=ids)
    #         for id in ids:
    #             status = Film.objects.get(id=id)
    #             print(status)
    #             # queryset = get_object_or_404(Film, pk__in=str(id))
    #             if int(status.checkstatus) == 1:
    #                     status.checkstatus^= 1
    #                     print(status.checkstatus)
    #                     status.save()
    #             # queryset = get_object_or_404(Film, pk__in= str(id))
    #         queryset = Film.objects.filter(pk__in=ids)
    #         # queryset = Film.objects.filter(checkstatus__in=str(0))
    #         return queryset
    #         # except:
    #         #     return Response({"status": "Notfound"})
    #     else:
    #         # Else no parameters, return all objects
    #         queryset = Film.objects.all()
    #         return queryset
    #         # return queryset
    #         # queryset = Film.objects.filter(checkstatus__in=str(1))

        # return queryset

    # def get_list_filter(self):
    #     queryset = Film.objects.all()
    #     # queryset = Film.objects.filter(checkstatus__in=str(1))
    #     print(queryset)
    #     return queryset


    
    def get_queryset(self):
        try:
            # Get URL parameter as a string, if exists 
            ids = self.request.query_params.get('ids', None)
            # print(ids)
            # Get snippets for ids if they exist
            if ids is not None:
                # Convert parameter string to list of integers
                ids = [ int(x) for x in ids.split(',') ]
                # Get objects for all parameter ids 
                # queryset = Film.objects.filter(pk__in=ids)
                for id in ids:
                    status = Film.objects.get(id=id)
                    print(status)
                    if int(status.checkstatus) == 1:
                            status.checkstatus^= 1
                            print(status.checkstatus)
                            status.save()
                    # queryset = get_object_or_404(Film, pk__in= str(id))
                queryset = Film.objects.filter(pk__in=ids)
                # queryset = Film.objects.filter(checkstatus__in=str(0))
                return queryset
            else:
                # Else no parameters, return all objects
                queryset = Film.objects.all()
                # queryset = Film.objects.filter(checkstatus__in=str(1))
                return queryset
        except:
            # return None
            return Response({
                "details": None
            }),



# def locations(request):


#     location_list = LocationChoiceField()

#     if request.GET.get('locations'):
#         selected_location = request.GET.get('locations')
#         details = Film.objects.filter(checkstatus=selected_location)
#     elif 'q' in request.GET:
#         q = request.GET['q']
#         # data = Film.objects.filter(filmurl__icontains=q)
#         multiple_q = Q(Q(year__icontains=q) | Q(filmurl__icontains=q))
#         details = Film.objects.filter(multiple_q)
#         # object=Film.objects.get(id=id)
#     # else:
#     #     details = Film.objects.all().order_by('-id')
#     else:
#         details = Film.objects.all().order_by('-id')


#     context = {
#         'query_results': details,
#         'location_list': location_list,

#     }
#     return render(request,'locations.html', context)


# date filterations


def convert_to_datetime(date_string):
    return dt.strptime(date_string, '%d-%m-%Y').date()

class CustomEmailleads_view(View):
    

    def get(self,  request):
   


        # if 'q' in request.GET:
        #     q = request.GET['q']
        #     # data = Film.objects.filter(filmurl__icontains=q)
        #     multiple_q = Q(Q(todaysdate__icontains=q) | Q(Subject__icontains=q) | Q(From_icontains=q) | Q(Received_Time_icontains=q) | Q(Email_Body_icontains=q))
        #     details = Customemailleads.objects.filter(multiple_q)
        #     # object=Film.objects.get(id=id)
        # elif request.GET.get('locations'):
        #     selected_location = request.GET.get('locations')
        #     details = Customemailleads.objects.filter(bcheckstatus=selected_location)
        # elif request.GET.get('label'):
        #     labels = request.GET.get('label')
        #     details = Customemailleads.objects.filter(bdropdownlist=labels)#.filter(dropdownlist='New')
        # elif request.GET.get('datesdata'):
        #     selected_datedata = request.GET.get('datesdata')
        #     details = Customemailleads.objects.filter(bdropdownlist='Benchsales',title=selected_datedata)
        # else:
        
        details = Customemailleads.objects.filter(checkstatus=1).order_by('-id')

            # details = Customemailleads.objects.order_by('-id')

        # # Parse the date string using dateutil.parser
        # day = parser.parse(received_time)

        # # Get the 'Date' and 'Time' components as strings with the desired format
        # date_str = day.strftime("%d-%m-%Y")
        page_number = request.GET.get('page', 1)
       
        # Create a Paginator object with your queryset and the number of items per page
        paginator = Paginator(details, 25)  # Change '10' to the number of items you want per page

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
        return render(request, 'customemaillead.html', context)

    def post(self, request, *args, **kwargs):

         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')

            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:

                    # obj = get_object_or_404(Customemailleads, id = id)
                    # obj.delete()
                    status = Customemailleads.objects.get(id=id)
                    # print(status)
                    status.checkstatus^= 1
                    status.save()
                return redirect('customemailleads')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = Customemailleads.objects.get(id=id)
                    print(status)
                    status.bcheckstatus^= 1
                    status.save()
                return redirect('customemailleads')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(Customemailleads, id=id)
                obj.delete()
                
                return redirect('customemailleads')
            else:
                return redirect('customemailleads')


class CustomEmailleadsopportunities_view(View):
    

    def get(self,  request):
        

        details = Customemailleads.objects.filter(checkstatus=0).order_by('-id')
        # details = Customemailleads.objects.order_by('-id')
          
 
        # # Parse the date string using dateutil.parser
        # day = parser.parse(received_time)

        # # Get the 'Date' and 'Time' components as strings with the desired format
        # date_str = day.strftime("%d-%m-%Y")
        page_number = request.GET.get('page', 1)
       
        # Create a Paginator object with your queryset and the number of items per page
        paginator = Paginator(details, 25)  # Change '10' to the number of items you want per page

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
        return render(request, 'customleadopportunities.html', context)

    def post(self, request, *args, **kwargs):

         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')

            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:

                    # obj = get_object_or_404(Customemailleads, id = id)
                    # obj.delete()
                    status = Customemailleads.objects.get(id=id)
                    # print(status)
                    status.checkstatus^= 1
                    status.save()
                return redirect('customemailleads')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = Customemailleads.objects.get(id=id)
                    print(status)
                    status.bcheckstatus^= 1
                    status.save()
                return redirect('customemailleads')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(Customemailleads, id=id)
                obj.delete()
                
                return redirect('customemailleads')
            else:
                return redirect('customemailleads')
# def customemailleadadd(request):
#     return render(request,'customemailleadadd.html')


# def customemailleadadd(request,id):
#     object=Customemailleads.objects.get(id=id)

def Customemailleadscreate(request):
    if request.method=="POST":
        # if 'save_home' in request.POST:
        #     leadfirstname=request.POST['leadfirstname']
        #     leadlastname=request.POST['leadlastname']
        #     leademail=request.POST['leademail']
        #     leadusername=request.POST['leadusername']
        #     leadpassword='Desss@123'
        #     leadcompany=request.POST['leadcompany']
        #     leadphonenumber=request.POST['leadphonenumber']
        #     leadaddress=request.POST['leadaddress']
        #     leadaddress2=request.POST['leadaddress2']
        #     leadcity=request.POST['leadcity']
        #     leadstate=request.POST['leadstate']
        #     leadzipcode=request.POST['leadzipcode']
        #     leadposition=request.POST['leadposition']
        #     leaddescription=request.POST['leaddescription']
        #     leadlocation = request.POST['leadlocation']
        #     leadduration = request.POST['leadduration']
        #     leadlegalstatus = request.POST['leadlegalstatus']
        #     leadinterviewtype = request.POST['leadinterviewtype']
        #     leadworktype = request.POST['leadworktype']
        #     leadremote = request.POST['leadremote']
        #     leadexperience = request.POST['leadexperience']
        #     leadrate = request.POST['leadrate']
        #     obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadposition=leadposition,leaddescription=leaddescription,
        #     leadlocation = leadlocation,leadduration = leadduration, leadlegalstatus = leadlegalstatus,leadinterviewtype = leadinterviewtype,leadworktype = leadworktype,leadremote = leadremote,
        #     leadexperience = leadexperience,leadrate = leadrate)
        #     obj.save()
        #     # return redirect('customemailleads')
        #     url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
        
        #                         # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
        #     response = requests.get(url)
        #     print(response.text)  # Print the response from the API

        #             # status = Emailbenchsales.objects.get(id=id)
        #             # print(status)
        #             # status.bcheckstatus^= 1
        #             # status.save()
        #     if response.status_code == 200:
        #         messages.success(request, 'Your lead has been updated to chiliadstaffing.com successfully!')  # Success message
        #         return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        #                     # return render(request, 'customemailleadsedits.html')
        #             # return redirect('custombenchsalesedits', id)
        #                     # return render(request, 'customemaillead.html')
        #                     # return redirect('customemailleadsedits', id)
        #     else:
        #         messages.error(request, 'No update was made. In our database, the data you provided has already been updated!')  # Error message
        #         return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        #                     # return render(request, 'customemailleadsedits.html')
        #             # return redirect('custombenchsalesedits', id)
        #         #return redirect('customemailleads')
        if 'chiliadstaffingapi' in request.POST:
            
            leadfirstname=request.POST['leadfirstname']
            leadlastname=request.POST['leadlastname']
            leademail=request.POST['leademail']
            leadusername=request.POST['leadusername']
            leadpassword='Desss@123'
            leadcompany=request.POST['leadcompany']
            leadphonenumber=request.POST['leadphonenumber']
            leadaddress=request.POST['leadaddress']
            leadaddress2=request.POST['leadaddress2']
            leadcity=request.POST['leadcity']
            leadstate=request.POST['leadstate']
            leadzipcode=request.POST['leadzipcode']
            # leadoccupation=request.POST['leadoccupation']
            # leaddescription=request.POST['leaddescription']
            # obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadoccupation=leadoccupation,leaddescription=leaddescription)
            leadposition=request.POST['leadposition']
            leaddescription=request.POST['leaddescription']
            leadlocation = request.POST['leadlocation']
            leadduration = request.POST['leadduration']
            leadlegalstatus = request.POST['leadlegalstatus']
            leadinterviewtype = request.POST['leadinterviewtype']
            leadworktype = request.POST['leadworktype']
            leadremote = request.POST['leadremote']
            leadexperience = request.POST['leadexperience']
            leadrate = request.POST['leadrate']
            obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadposition=leadposition,leaddescription=leaddescription,
            leadlocation = leadlocation,leadduration = leadduration, leadlegalstatus = leadlegalstatus,leadinterviewtype = leadinterviewtype,leadworktype = leadworktype,leadremote = leadremote,
            leadexperience = leadexperience,leadrate = leadrate)
            obj.save()
            # print(leademail)
            

            # soup = BeautifulSoup(leaddescription, 'html.parser')
            # leaddescriptiontext = soup.get_text()
            # print(leaddescriptiontext)
            # unwanted = "[%]"
            # originaldata = re.sub(unwanted, '', leaddescription)
                            
            # title = my_model.title
            # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}"
            #url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescriptiontext}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
            url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
            # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
            response = requests.get(url)
            print(response.text)  # Print the response from the API
                            # status = Emailbenchsales.objects.get(id=id)
                            # print(status)
                            # status.bcheckstatus^= 1
                            # status.save()
            if response.status_code == 200:
                        
                            messages.success(request, 'Your lead has been updated to chiliadstaffing.com successfully!')  # Success message
                            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                            # return render(request, 'customemailleadsedits.html')
                            # return redirect('custombenchsalesedits', id)
                            # return render(request, 'customemaillead.html')
                            # return redirect('customemailleadsedits', id)
            elif response.status_code == 403:
                        
                            # messages.success(request, 'No update was made. In our database, the data you provided has already been updated!')  # Success message
                            messages.success(request, 'Lead update was made. In our database, the job data you provided has already been updated!')
                            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                messages.error(request, 'Your lead has not been updated to chiliadstaffing.com!')  # Error message
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                            # return render(request, 'customemailleadsedits.html')
                # return redirect('custombenchsalesedits', id)
            return redirect('customemailleads')
                            # return redirect('search')
            # return redirect('customemailleads')

                        
        elif 'careerdesssapi' in request.POST:
                leadfirstname=request.POST['leadfirstname']
                leadlastname=request.POST['leadlastname']
                leademail=request.POST['leademail']
                leadusername=request.POST['leadusername']
                leadpassword='Desss@123'
                leadcompany=request.POST['leadcompany']
                leadphonenumber=request.POST['leadphonenumber']
                leadaddress=request.POST['leadaddress']
                leadaddress2=request.POST['leadaddress2']
                leadcity=request.POST['leadcity']
                leadstate=request.POST['leadstate']
                leadzipcode=request.POST['leadzipcode']
                
                leadposition=request.POST['leadposition']
                leaddescription=request.POST['leaddescription']
                leadlocation = request.POST['leadlocation']
                leadduration = request.POST['leadduration']
                leadlegalstatus = request.POST['leadlegalstatus']
                leadinterviewtype = request.POST['leadinterviewtype']
                leadworktype = request.POST['leadworktype']
                leadremote = request.POST['leadremote']
                leadexperience = request.POST['leadexperience']
                leadrate = request.POST['leadrate']
                # new data fields
                leadskills1 = request.POST['leadskills1']
                leadexperience1 = request.POST['leadexperience1']
                leadskills2 = request.POST['leadskills2']
                leadexperience2 = request.POST['leadexperience2']
                leadskills3 = request.POST['leadskills3']
                leadexperience3 = request.POST['leadexperience3']
                leadskills4 = request.POST['leadskills4']
                leadexperience4 = request.POST['leadexperience4']
                leadskills5 = request.POST['leadskills5']
                leadexperience5 = request.POST['leadexperience5']
                emailleadid = request.POST['emailleadid']
                #print(leademail)
                obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadposition=leadposition,leaddescription=leaddescription,
                leadlocation = leadlocation,leadduration = leadduration, leadlegalstatus = leadlegalstatus,leadinterviewtype = leadinterviewtype,leadworktype = leadworktype,leadremote = leadremote,
                leadexperience = leadexperience,leadrate = leadrate,  leadskills1 = leadskills1,leadexperience1 = leadexperience1, leadskills2 = leadskills2,leadexperience2 = leadexperience2, leadskills3 = leadskills3, leadexperience3 = leadexperience3, leadskills4 = leadskills4, leadexperience4 = leadexperience4, leadskills5 =leadskills5,
                leadexperience5 = leadexperience5,)
                obj.save()
                # django inbuilt function for removing html tags
                leaddescriptiontext1 = strip_tags(leaddescription).strip()
                leaddescriptiontext  = leaddescriptiontext1.replace("'", "")
               
                print(leadlocation)
                print(leadexperience)
      
                                
               
                # print(type(testdescription))
                
                # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescriptiontext}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
                              
            

                # URL for the API endpoint
                url = "https://career.desss.com/dynamic/careerdesssapi.php?action=employer_lead"

                # Sample data as a dictionary
                data = {
                'firstname':leadfirstname,
                'lastname':leadlastname,
                'email':leademail,
                'username':leadusername,
                'password':leadpassword,
                'company':leadcompany,
                'phonenumber':leadphonenumber,
                'address':leadaddress,
                'address2':leadaddress2,
                'city':leadcity,
                'state':leadstate,
                'zipcode':leadzipcode,
                'occupation':leadposition,
                'description':leaddescriptiontext,
                'leadlocation':leadlocation,
                'leadduration':leadduration,
                'leadlegalstatus':leadlegalstatus,
                'leadinterviewtype':leadinterviewtype,
                'leadworktype':leadworktype,
                'leadremote':leadremote,
                'leadexperience':leadexperience,
                'leadrate':leadrate,
                'leadskills1' : leadskills1,
                'leadexperience1' : leadexperience1,
                'leadskills2' : leadskills2,
                'leadexperience2' : leadexperience2,
                'leadskills3' : leadskills3,
                'leadexperience3' : leadexperience3,
                'leadskills4' : leadskills4,
                'leadexperience4' : leadexperience4,
                'leadskills5' : leadskills5,
                'leadexperience5' : leadexperience5,
                    # Add more key-value pairs as needed
                }
                print(data)

                # Sending a POST request with the data
                response = requests.post(url, data=data)

                # Check the response from the server


                print(response.text)  # Print the response from the API
                #print(url)
                    # status = Emailbenchsales.objects.get(id=id)
                    # print(status)
                    # status.bcheckstatus^= 1
                    # status.save()
                
                if response.status_code == 200:
                    id = emailleadid
                    status = Customemailleads.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                    messages.success(request, 'Your lead has been updated to Career.desss.com successfully!')  # Success message
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                            # return render(request, 'customemailleadsedits.html')
                    # return redirect('custombenchsalesedits', id)
                            # return render(request, 'customemaillead.html')
                            # return redirect('customemailleadsedits', id)
                elif response.status_code == 403:
                    id = emailleadid
                    status = Customemailleads.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                    # messages.success(request, 'Lead update was made. In our database, the job data you provided has already been updated!')  # Success message
                    # messages.success(request, 'Your lead updated successfully. In our database, the job data you provided has already been updated!')
                    messages.success(request, 'Your lead updated. In our database, the job data you provided has already been updated!')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                else:
                    messages.error(request, 'Your lead has not been updated to Career.desss.com!')  # Error message
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                            # return render(request, 'customemailleadsedits.html')
                    # return redirect('custombenchsalesedits', id)
                #return redirect('customemailleads')
                                # return redirect('search')
                #   return redirect('emailbenchsalesedit', id)
        # else:
        #     form = EmailbenchsalesForm(instance=my_model)
        #     return redirect(request.META['HTTP_REFERER'])
        # return redirect('customemailleads')



class CustomBenchsales_view(View):
    

    def get(self,  request):
   
        


        # if 'q' in request.GET:
        #     q = request.GET['q']
        #     # data = Film.objects.filter(filmurl__icontains=q)
        #     multiple_q = Q(Q(bstodaysdate__icontains=q) | Q(bsSubject__icontains=q) | Q(bsFrom_icontains=q) | Q(bsReceived_Time_icontains=q) | Q(bsEmail_Body_icontains=q))
        #     details = Custombenchsales.objects.filter(multiple_q)
        #     # object=Film.objects.get(id=id)
        # elif request.GET.get('locations'):
        #     selected_location = request.GET.get('locations')
        #     details = Custombenchsales.objects.filter(bcheckstatus=selected_location)
        # elif request.GET.get('label'):
        #     labels = request.GET.get('label')
        #     details = Custombenchsales.objects.filter(bdropdownlist=labels)#.filter(dropdownlist='New')
        # elif request.GET.get('datesdata'):
        #     selected_datedata = request.GET.get('datesdata')
        #     details = Custombenchsales.objects.filter(bdropdownlist='Benchsales',title=selected_datedata)
        # else:
        


        details = Custombenchsales.objects.filter(bscheckstatus=1).order_by('-id')
            # details = Custombenchsales.objects.order_by('-id')
            # print(details)        
        page_number = request.GET.get('page', 1)

        # Create a Paginator object with your queryset and the number of items per page
        paginator = Paginator(details, 25)  # Change '10' to the number of items you want per page

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
        return render(request, 'custombenchsales.html', context)

    def post(self, request, *args, **kwargs):

         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')

            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:

                    # obj = get_object_or_404(Custombenchsales, id = id)
                    # obj.delete()
                    status = Custombenchsales.objects.get(id=id)
                    # print(status)
                    status.bscheckstatus^= 1
                    status.save()
                return redirect('custombenchsales')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = Custombenchsales.objects.get(id=id)
                    print(status)
                    status.bcheckstatus^= 1
                    status.save()
                return redirect('custombenchsales')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(Custombenchsales, id=id)
                obj.delete()
                
                return redirect('custombenchsales')
            else:
                return redirect('custombenchsales')

def custombenchsalesadd(request):
    return render(request,'custombenchsalesadd.html')

# def Custombenchsalescreate(request):
#     # if request.method=="POST":
#     if 'save_home' in request.POST:
#         benchfirstname=request.POST['benchfirstname']
#         benchlastname=request.POST['benchlastname']
#         benchexperience=request.POST['benchexperience']
#         benchcurrentlocation=request.POST['benchcurrentlocation']
#         benchtechnology=request.POST['benchtechnology']
#         benchrelocation=request.POST['benchrelocation']
#         benchvisa=request.POST['benchvisa']
#         benchnoticeperiod=request.POST['benchnoticeperiod']
#         benchsalesfirstname=request.POST['benchsalesfirstname']
#         benchsaleslastname=request.POST['benchsaleslastname']
#         benchsalescompany=request.POST['benchsalescompany']
#         benchsalesemail=request.POST['benchsalesemail']
#         benchsalesmobile=request.POST['benchsalesmobile']
#         benchsalesaddress=request.POST['benchsalesaddress']

#         obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,benchcurrentlocation=benchcurrentlocation,benchtechnology=benchtechnology,benchrelocation=benchrelocation,benchvisa=benchvisa,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress)
#         obj.save()

#         return redirect('custombenchsales')
        
#     elif 'chiliadstaffingapi' in request.POST:
#         benchfirstname=request.POST['benchfirstname']
#         benchlastname=request.POST['benchlastname']
#         benchexperience=request.POST['benchexperience']
#         benchcurrentlocation=request.POST['benchcurrentlocation']
#         benchtechnology=request.POST['benchtechnology']
#         benchrelocation=request.POST['benchrelocation']
#         benchvisa=request.POST['benchvisa']
#         benchnoticeperiod=request.POST['benchnoticeperiod']
#         benchsalesfirstname=request.POST['benchsalesfirstname']
#         benchsaleslastname=request.POST['benchsaleslastname']
#         benchsalescompany=request.POST['benchsalescompany']
#         benchsalesemail=request.POST['benchsalesemail']
#         benchsalesmobile=request.POST['benchsalesmobile']
#         benchsalesaddress=request.POST['benchsalesaddress']

#         obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,benchcurrentlocation=benchcurrentlocation,benchtechnology=benchtechnology,benchrelocation=benchrelocation,benchvisa=benchvisa,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress)
#         obj.save()
 
                        
#         # title = my_model.title
#         url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&currentlocation={benchcurrentlocation}&technology={benchtechnology}&relocation={benchrelocation}&visa={benchvisa}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"

#         response = requests.get(url)
#         print(response.text)  # Print the response from the API

#         return redirect('custombenchsales')
from urllib.parse import urlencode

def Custombenchsalescreate(request):
    if request.method=="POST":
        if 'careerdesssapi' in request.POST:
            indexhorizontal = request.POST['indexhorizontal']
            indexvertical = request.POST['indexvertical']
            if int(indexhorizontal) == 1:
                #need to handle in try and except
                benchfirstname=request.POST['benchfirstname']
                benchlastname=request.POST['benchlastname']
                benchexperience=request.POST['benchexperience']
                Rate=request.POST['Rate']
                # benchcurrentlocation=request.POST['benchcurrentlocation']
                # benchtechnology=request.POST['benchtechnology']
                Position=request.POST['Position']
                Location=request.POST['Location']
                Duration=request.POST['Duration']
                benchrelocation=request.POST['benchrelocation']
                Legal_Status=request.POST['Legal_Status']
                benchnoticeperiod=request.POST['benchnoticeperiod']
                benchsalesfirstname=request.POST['benchsalesfirstname']
                benchsaleslastname=request.POST['benchsaleslastname']
                benchsalescompany=request.POST['benchsalescompany']
                benchsalesemail=request.POST['benchsalesemail']
                benchsalesmobile=request.POST['benchsalesmobile']
                benchsalesaddress=request.POST['benchsalesaddress']
                Interview_Type=request.POST['Interview_Type']
                Work_Type=request.POST['Work_Type']
                Remote=request.POST['Remote']
                print('processing bechsales only')

                url_with_params = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&Rate={Rate}&Position={Position}&Location={Location}&Duration={Duration}&relocation={benchrelocation}&Legal_Status={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}"
                b = requests.get(url_with_params)
                # return HttpResponse(url_with_params)       
                return redirect('custombenchsales')
     
                # return HttpResponse('processing bechsales only')   
            else:
                benchfirstname=request.POST['benchfirstname']
                benchlastname=request.POST['benchlastname']
                benchexperience=request.POST['benchexperience']
                Rate=request.POST['Rate']
                # benchcurrentlocation=request.POST['benchcurrentlocation']
                # benchtechnology=request.POST['benchtechnology']
                Position=request.POST['Position']
                Location=request.POST['Location']
                Duration=request.POST['Duration']
                benchrelocation=request.POST['benchrelocation']
                Legal_Status=request.POST['Legal_Status']
                benchnoticeperiod=request.POST['benchnoticeperiod']
                benchsalesfirstname=request.POST['benchsalesfirstname']
                benchsaleslastname=request.POST['benchsaleslastname']
                benchsalescompany=request.POST['benchsalescompany']
                benchsalesemail=request.POST['benchsalesemail']
                benchsalesmobile=request.POST['benchsalesmobile']
                benchsalesaddress=request.POST['benchsalesaddress']
                Interview_Type=request.POST['Interview_Type']
                Work_Type=request.POST['Work_Type']
                Remote=request.POST['Remote']
                

                # obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress,Interview_Type=Interview_Type,Work_Type=Work_Type,Remote=Remote)
                # obj.save()
                #Method 1
                # a = []
                # for i in range(int(indexhorizontal)):
                #     for j in range(int(indexvertical)-1):
                # # for i in range(len(data)):
                # #     for j in range(len(data[0])):
                #         tablesdataset=request.POST[f'table{i}_{j}']
                #         a.append(tablesdataset)
                #         # print(benchfirstname)
                #         # print(f'table{i}_{j}')
                url_base ='https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead'
                # print(a)
                a = []
                for i in range(1, int(indexhorizontal)):
                    try:
                        # for j in range(int(indexvertical)-1):
                    # for i in range(len(data)):
                    #     for j in range(len(data[0])):
                        nametable=request.POST[f'table1_{i}']
                        # Add your condition to exclude rows based on the 'Name'
                        # if nametable == 'Name':
                        #     continue  # Skip this row and move to the next iteration                   
                        experiencetable = request.POST[f'table2_{i}']
                        locationtable = request.POST[f'table3_{i}']
                        technologytable=request.POST[f'table4_{i}']                                    
                        relocationtable = request.POST[f'table5_{i}']
                        visatable = request.POST[f'table6_{i}']  
                        available = request.POST[f'table7_{i}']

                    except:
                        nametable= request.POST['benchfirstname']                                 
                        experiencetable = request.POST['benchexperience']
                        locationtable = request.POST['Location']
                        technologytable= request.POST['Position']                         
                        relocationtable = request.POST['benchrelocation']
                        visatable = request.POST['Legal_Status']
                        available = request.POST['benchnoticeperiod']
                    print(nametable)
                    print(experiencetable)
                    print(locationtable)
                    print(technologytable)
                    print(relocationtable)
                    print(visatable)
                    print(available)
                    

                


                    # url_with_params = f'{url_base}&firstname={nametable}&lastname={benchlastname}&experience={experiencetable}&Rate={Rate}&Position={Position}&Location={locationtable}&Duration={Duration}&relocation={relocationtable}&Legal_Status={visatable}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}&name={tablesdataset}&=visa={visatable}&=experience={experiencetable}&=location={locationtable}&=relocation={relocationtable}'
                    url_with_params = f'{url_base}&firstname={nametable}&lastname={benchlastname}&experience={experiencetable}&Rate={Rate}&Position={technologytable}&Location={locationtable}&Duration={Duration}&relocation={relocationtable}&Legal_Status={visatable}&noticeperiod={available}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}'
                    b = requests.get(url_with_params)
                    a.append(nametable)
                        # print(benchfirstname)
                        # print(f'table{i}_{j}')
                        
                # print(a)
               
                
                return redirect('custombenchsales')
                    
                    
               
                # return HttpResponse(url_with_params)        
        elif 'careerdesssapi1' in request.POST:
            indexhorizontal = request.POST['indexhorizontal']
            indexvertical = request.POST['indexvertical']
            if int(indexhorizontal) == 1:
                #need to handle in try and except
                benchfirstname=request.POST['benchfirstname']
                benchlastname=request.POST['benchlastname']
                benchexperience=request.POST['benchexperience']
                Rate=request.POST['Rate']
                # benchcurrentlocation=request.POST['benchcurrentlocation']
                # benchtechnology=request.POST['benchtechnology']
                Position=request.POST['Position']
                Location=request.POST['Location']
                Duration=request.POST['Duration']
                benchrelocation=request.POST['benchrelocation']
                Legal_Status=request.POST['Legal_Status']
                benchnoticeperiod=request.POST['benchnoticeperiod']
                benchsalesfirstname=request.POST['benchsalesfirstname']
                benchsaleslastname=request.POST['benchsaleslastname']
                benchsalescompany=request.POST['benchsalescompany']
                benchsalesemail=request.POST['benchsalesemail']
                benchsalesmobile=request.POST['benchsalesmobile']
                benchsalesaddress=request.POST['benchsalesaddress']
                Interview_Type=request.POST['Interview_Type']
                Work_Type=request.POST['Work_Type']
                Remote=request.POST['Remote']
                print('processing bechsales only')
                return HttpResponse('processing bechsales only')   
            else:
                benchfirstname=request.POST['benchfirstname']
                benchlastname=request.POST['benchlastname']
                benchexperience=request.POST['benchexperience']
                Rate=request.POST['Rate']
                # benchcurrentlocation=request.POST['benchcurrentlocation']
                # benchtechnology=request.POST['benchtechnology']
                Position=request.POST['Position']
                Location=request.POST['Location']
                Duration=request.POST['Duration']
                benchrelocation=request.POST['benchrelocation']
                Legal_Status=request.POST['Legal_Status']
                benchnoticeperiod=request.POST['benchnoticeperiod']
                benchsalesfirstname=request.POST['benchsalesfirstname']
                benchsaleslastname=request.POST['benchsaleslastname']
                benchsalescompany=request.POST['benchsalescompany']
                benchsalesemail=request.POST['benchsalesemail']
                benchsalesmobile=request.POST['benchsalesmobile']
                benchsalesaddress=request.POST['benchsalesaddress']
                Interview_Type=request.POST['Interview_Type']
                Work_Type=request.POST['Work_Type']
                Remote=request.POST['Remote']
                

                # obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress,Interview_Type=Interview_Type,Work_Type=Work_Type,Remote=Remote)
                # obj.save()
                #Method 1
                a = []
                for i in range(int(indexhorizontal)):
                    for j in range(int(indexvertical)-1):
                # for i in range(len(data)):
                #     for j in range(len(data[0])):
                        tablesdataset=request.POST[f'table{i}_{j}']
                        a.append(tablesdataset)
                        # print(benchfirstname)
                        # print(f'table{i}_{j}')
                        
                print(a)
                # Split the 'a' list into sublists based on 'indexvertical'
                sublists = [a[i:i + (int(indexvertical) - 1)] for i in range(0, len(a), int(indexvertical) - 1)]
                # Construct the URL with query parameters
                # url_base = 'http://sample.com'
                url_base ='https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead'
                query_params = []

                # for idx, sublist in enumerate(sublists):
                #     param_name = f'b{idx}'
                #     param_value = '-'.join(sublist)
                #     query_params.append(f'{param_name}={param_value}')
                for idx, sublist in enumerate(sublists):
                    param_name = f'b{idx}'
                    param_value = '-'.join(sublist)
                    
                    query_params.append(f'{param_name}={param_value}')

                # url_with_params = f'{url_base}?{"&".join(query_params)}'
                url_with_params = f'{url_base}&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&Rate={Rate}&Position={Position}&Location={Location}&Duration={Duration}&relocation={benchrelocation}&Legal_Status={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}{"&".join(query_params)}'
                #Method 2
                # a =[]
                # for i in range(int(indexhorizontal)):
                #     for j in range(int(indexvertical) - 1):
                #         benchfirstname = request.POST[f'table{i}_{j}']
                #         a.append(benchfirstname)

               
                # # Split the 'a' list into sublists based on 'indexvertical'
                # sublists = [a[i:i + (int(indexvertical) - 1)] for i in range(0, len(a), int(indexvertical) - 1)]

                # # Create a JSON object from sublists
                # # data_to_send = {
                # #     f'b{idx}': sublist for idx, sublist in enumerate(sublists)
                # # }
                # query_params = []
                # for idx, sublist in enumerate(sublists):
                #     param_name = f'b{idx}'
                #     param_value = '-'.join(sublist)
                #     query_params.append(f'{param_name}={param_value}')

                # # URL to send the POST request to
                # url = 'http://sample.com'

                # # Send a POST request with JSON data in the request body
                # response = requests.post(url, json=query_params)

                # Print the response status code
                # print(response.status_code)
               
                return HttpResponse(url_with_params)        
        return redirect('custombenchsales')
    # return HttpResponse('hello')
    return redirect('custombenchsales')
    # if request.method=="POST":
    # if 'save_home' in request.POST:
    #     benchfirstname=request.POST['benchfirstname']
    #     benchlastname=request.POST['benchlastname']
    #     benchexperience=request.POST['benchexperience']
    #     Rate=request.POST['Rate']
    #     # benchcurrentlocation=request.POST['benchcurrentlocation']
    #     # benchtechnology=request.POST['benchtechnology']
    #     Position=request.POST['Position']
    #     Location=request.POST['Location']
    #     Duration=request.POST['Duration']
    #     benchrelocation=request.POST['benchrelocation']
    #     Legal_Status=request.POST['Legal_Status']
    #     benchnoticeperiod=request.POST['benchnoticeperiod']
    #     benchsalesfirstname=request.POST['benchsalesfirstname']
    #     benchsaleslastname=request.POST['benchsaleslastname']
    #     benchsalescompany=request.POST['benchsalescompany']
    #     benchsalesemail=request.POST['benchsalesemail']
    #     benchsalesmobile=request.POST['benchsalesmobile']
    #     benchsalesaddress=request.POST['benchsalesaddress']
    #     Interview_Type=request.POST['Interview_Type']
    #     Work_Type=request.POST['Work_Type']
    #     Remote=request.POST['Remote']

    #     obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress,Interview_Type=Interview_Type,Work_Type=Work_Type,Remote=Remote)
    #     obj.save()

    #     return redirect('custombenchsales')
        
    # elif 'chiliadstaffingapi' in request.POST:
    #     benchfirstname=request.POST['benchfirstname']
    #     benchlastname=request.POST['benchlastname']
    #     benchexperience=request.POST['benchexperience']
    #     Rate=request.POST['Rate']
    #     # benchcurrentlocation=request.POST['benchcurrentlocation']
    #     # benchtechnology=request.POST['benchtechnology']
    #     Position=request.POST['Position']
    #     Location=request.POST['Location']
    #     Duration=request.POST['Duration']
    #     benchrelocation=request.POST['benchrelocation']
    #     Legal_Status=request.POST['Legal_Status']
    #     benchnoticeperiod=request.POST['benchnoticeperiod']
    #     benchsalesfirstname=request.POST['benchsalesfirstname']
    #     benchsaleslastname=request.POST['benchsaleslastname']
    #     benchsalescompany=request.POST['benchsalescompany']
    #     benchsalesemail=request.POST['benchsalesemail']
    #     benchsalesmobile=request.POST['benchsalesmobile']
    #     benchsalesaddress=request.POST['benchsalesaddress']
    #     Interview_Type=request.POST['Interview_Type']
    #     Work_Type=request.POST['Work_Type']
    #     Remote=request.POST['Remote']

    #     obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress,Interview_Type=Interview_Type,Work_Type=Work_Type,Remote=Remote)
    #     obj.save()
 
                        
    #     # title = my_model.title
    #     url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&Rate={Rate}&Position={Position}&Location={Location}&Duration={Duration}&relocation={benchrelocation}&Legal_Status={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}"

    #     response = requests.get(url)
    #     print(response.text)  # Print the response from the API

    #     return redirect('custombenchsales')

                    
    # elif 'careerdesssapi' in request.POST:
        # benchfirstname=request.POST['benchfirstname']
        # benchlastname=request.POST['benchlastname']
        # benchexperience=request.POST['benchexperience']
        # Rate=request.POST['Rate']
        # # benchcurrentlocation=request.POST['benchcurrentlocation']
        # # benchtechnology=request.POST['benchtechnology']
        # Position=request.POST['Position']
        # Location=request.POST['Location']
        # Duration=request.POST['Duration']
        # benchrelocation=request.POST['benchrelocation']
        # Legal_Status=request.POST['Legal_Status']
        # benchnoticeperiod=request.POST['benchnoticeperiod']
        # benchsalesfirstname=request.POST['benchsalesfirstname']
        # benchsaleslastname=request.POST['benchsaleslastname']
        # benchsalescompany=request.POST['benchsalescompany']
        # benchsalesemail=request.POST['benchsalesemail']
        # benchsalesmobile=request.POST['benchsalesmobile']
        # benchsalesaddress=request.POST['benchsalesaddress']
        # Interview_Type=request.POST['Interview_Type']
        # Work_Type=request.POST['Work_Type']
        # Remote=request.POST['Remote']
        # table=request.POST['table1']
        # print(table)

        # # obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress,Interview_Type=Interview_Type,Work_Type=Work_Type,Remote=Remote)
        # # obj.save()
                            
        #                     # title = my_model.title
        # # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&currentlocation={Location}&technology={Position}&relocation={benchrelocation}&visa={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"

        # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&Rate={Rate}&Position={Position}&Location={Location}&Duration={Duration}&relocation={benchrelocation}&Legal_Status={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}"
     
     
        # # response = requests.get(url)
        # # print(response.text)  # Print the response from the API

        # return redirect('custombenchsales')

                    
    
    
    

# def custombenchsalesedits(request,id):
#     object=Custombenchsales.objects.get(id=id)
#     print(object.bsEmail_Body)
#     content = object.bsEmail_Body
    
#     # Load spaCy's English NLP model
#     nlp = spacy.load('en_core_web_sm')

#     # Define the pattern to extract the tabular data
#     pattern = r"(\d+)\s+([^\n]+)\n+(\d+\+?)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)"

#     # Find all matches using the pattern
#     matches = re.findall(pattern, content)

#     # Prepare the extracted tabular data as a list of dictionaries
#     extracted_data = []
#     for match in matches:
#         s_no, technology, exp, visa, location, relocation = match
#         extracted_data.append({
#             "S. No": s_no.strip(),
#             "Technology": technology.strip(),
#             "Exp": exp.strip(),
#             "Visa": visa.strip(),
#             "Location": location.strip(),
#             "Relocation": relocation.strip(),
#             "First Name": "",
#             "Last Name": "",
#             "Mobile": "",
#             "Email ID": "",
#             "Company Name": "",
#             "Company Address": ""
#         })

#     # Process the email text with spaCy for NER
#     doc = nlp(content)

#     # Initialize variables to store the extracted "From" address and the last email data
#     from_address = ""
#     last_email_data = ""

#     # Extract "From" address and the last email data
#     for sent in doc.sents:
#         if "From:" in sent.text:
#             from_address = sent.text.replace("From:", "").strip()
#         last_email_data = sent.text.strip()

#     # Extract named entities (PERSON, PHONE, EMAIL, ORG) from the processed text
#     # Define the regex patterns to extract the required details
#     name_pattern = r'From:\s+(.*?)\s+(.*?)\n'
#     position_pattern = r'\s+(.*?)\s+(.*?)\n\s*(?:[Aa]t|AT|@)\s.*'
#     phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b|\b\d{10}\b'
#     email_pattern = r'[\w\.-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}'
#     address_pattern = r'[A-Za-z]+(?:,[A-Za-z]+)*(?:\s*,\s*\d{5})?\s*,\s*[A-Za-z]+\s*,\s*[A-Za-z]+\s*,\s*\d{5}\b'
#     thanks_pattern = r'(?:Thanks\s*&(?:amp;)?\s*regards|Thanks\s*and\s*Regards),\s*(.*?)\s+([A-Za-z]+)'

#     # Find the matches using the regex patterns
#     name_match = re.search(name_pattern, content)
#     position_match = re.search(position_pattern, content)
#     phone_matches = re.findall(phone_pattern, content)
#     email_match = re.search(email_pattern, content)
#     address_match = re.search(address_pattern, content)
#     thanks_match = re.search(thanks_pattern, content)

#     # Extract the relevant details from the matches if a match is found
#     first_name = name_match.group(1) if name_match else ""
#     last_name = name_match.group(2) if name_match else ""
#     position = position_match.group(1) if position_match else ""
#     phone = next((num for num in phone_matches if len(num) == 10), "")
#     email = email_match.group() if email_match else ""
#     address = address_match.group() if address_match else ""

#     # If the name is not found in the "From" field, extract it from the "Thanks & regards" section
#     if not first_name and not last_name and thanks_match:
#         first_name = thanks_match.group(1)
#         last_name = thanks_match.group(2)

#     # Extract the company name from the email ID (if provided) and remove ".com" or any other characters after the dot (".") symbol
#     if email:
#         company_name_match = re.search(r'@([^\s.]+)', email)
#         if company_name_match:
#             company_name = company_name_match.group(1)
#             company_name = company_name.split(".")[0]  # Remove ".com" or any other characters after the dot
#     else:
#         company_name = ""

#     # Output the extracted data (NER and tabular data)
#     print("First Name:", first_name)
#     print("Last Name:", last_name)
#     print("Mobile:", phone)
#     print("Email ID:", email)
#     print("Address:", address)
#     print("Company Name:", company_name)

#     # Specify the CSV file name
#     emailcsv_file =  dot + str("extracted_data.csv")

#     # Write the extracted data to a CSV file
#     with open(emailcsv_file, mode='w', newline='') as file:
#         writer = csv.writer(file)

#         writer.writerow(["First Name", "Last Name", "Mobile", "Email ID", "Company Name", "Company Address", "S. No", "Technology", "Exp", "Visa", "Location", "Relocation"])

#         # Combine the NER data with tabular data in each row
#         for data in extracted_data:
#             print(data)
#             row = [
#                 first_name if data["First Name"] == "" else data["First Name"],
#                 last_name if data["Last Name"] == "" else data["Last Name"],
#                 phone if data["Mobile"] == "" else data["Mobile"],
#                 email if data["Email ID"] == "" else data["Email ID"],
#                 company_name if data["Company Name"] == "" else data["Company Name"],
#                 address if data["Company Address"] == "" else data["Company Address"],
#                 data["S. No"],
#                 data["Technology"],
#                 data["Exp"],
#                 data["Visa"],
#                 data["Location"],
#                 data["Relocation"]
#             ]
#             writer.writerow(row)

#     print("Data saved to", emailcsv_file)


#     # return HttpResponse("hello world")
#     return HttpResponse(object.bsEmail_Body)
    # return render(request,'custombenchsalesedits.html',{'object':object,})

# def extract_data(cell):
#     lines = cell.find_all(text=True)
#     if len(lines) > 2:
#         return '\n'.join(lines[:2]) + '...'
#     return '\n'.join(lines)


def extract_table_data_text(html_content):
    try:
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all table rows () in the HTML content
        table_rows = soup.find_all('tr')

        # Extract text from table data cells () in each row
        table_data_texts = []
        for row in table_rows:
            table_data = row.find_all('td')
            row_text = [cell.get_text().strip() for cell in table_data]

            # Filter out unwanted rows (headers and footer) based on row length
            if len(row_text) in [5, 6, 7, 8, 9, 10]:
            # if len(row_text) in [8]:
            # if len(row_text) in [6]:

                # Exclude rows that start with specific strings
                if not any(cell.startswith("Hello Everyone") or cell.startswith("Hello") or cell.startswith("None") for cell in row_text):
                    table_data_texts.append(row_text)

        return table_data_texts

    except Exception as e:
        print(f"Error while parsing the HTML content: {e}")
        return []
def extract_data(cell):
    lines = cell.find_all(text=True)
    if len(lines) > 1:
        # return '\n'.join(lines[:1]) + '...'
        return 'None'
    return '\n'.join(lines)
    # return 'None'



def custombenchsalesedits(request,id):
    # if request.method=="GET":

    # object_bench=Custombench.objects.get(id=id)

   
    # return render(request,'customemailleadsedits.html',{'object':object,})
    object_bench=Custombenchsales.objects.get(id=id)
    
    #print(object.bsEmail_Bodyhtml)
    content = object_bench.bsEmail_Bodyhtml
    # html_content = row[4]
    # html_content = content
    table_data_texts = extract_table_data_text(content)
    # print(table_data_texts)
        # Append the extracted data to the list

    df = pd.DataFrame(table_data_texts)
    # df = pd.DataFrame(data)
        # csv_filename = f'table_data_{idx}.csv'  # Generate a unique CSV file name for each row
        # df.to_csv(csv_filename, index=False)

    csv_filename = dot +str('table_data.csv')


    emailcontent = object_bench.bsEmail_Body
    # Define the patterns to match
    patterns = [
        "E-Verified Company",
        "Thanks and Regards,",
        "Thanks & Regards",
        "Thanks & Regards..!!!",
        "Thanks & regards,",
        "Regards,",
        "Regards",
        # "Contact Info...!!",
        "Thanks and Regards",
        "Thanking you and looking forward to a beneficial relationship…!!",
        # "e>",
        "Thanks,"
    ]
    
    # Find the starting point based on the patterns
    start = None
    for pattern in patterns:
        if pattern in emailcontent:
            start = emailcontent.index(pattern)
            break

    # Extract the name after the pattern
    if start is not None:
        name_match = re.search(r'\n(.+)', emailcontent[start:])
        if name_match:
            full_name = name_match.group(1).strip()

            # Remove position information from the name
            position_removed_name = re.sub(r'-[^-]+$', '', full_name).strip()
            # position_removed_name = re.sub(r'-.*?-', '', full_name).strip()
            name_parts = position_removed_name.split()

            # name_parts = full_name.split()

            # Split the full name into first name and last name
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
            elif len(name_parts) == 1:
                first_name = name_parts[0]
                last_name = ""
            else:
                first_name = ""
                last_name = ""

            print("First Name:", first_name)
            print("Last Name:", last_name)

        else:
            # print("No employer name found.")
            first_name = ""
            last_name = ""
    else:
        first_name = ""
        last_name = ""
        print("First Name:", first_name)
        print("Last Name:", last_name)

    # Extract the email address after the pattern
    if start is not None:
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', emailcontent[start:])
        if email_match:
            email_id = email_match.group()
            print("Email ID:", email_id)
        else:
            # Find email addresses with potential spaces before or after the "@" symbol
            email_matches = re.findall(r'[\w\.-]+ ?@ ?[\w\.-]+', emailcontent)
            if email_matches:
                for email in email_matches:
                    email_id = email.replace(" ", "")  # Remove spaces from the extracted email
                    print("Email ID:", email_id)
            else:
                email_id = ""
                print("Email:", email_id)
    else:
        email_id = ""
        print("Email:", email_id)

    if start is not None:
        phone_match = re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', emailcontent[start:])
        if phone_match:
            phone_number = phone_match.group()
            print("Phone Number:", phone_number)
        else:
            # Extract phone number with parentheses
            phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', emailcontent[start:])
            if phone_match:
                phone_number = phone_match.group()
                print("Phone Number:", phone_number)
            else:
                phone_number = ""
                # print("No phone number found.")
    else:
        phone_number = ""
        # print("No pattern found.")



    try:
        # Try to read the CSV file
       # df = pd.read_csv(csv_filename, encoding='utf8', header=None, dtype=str)
        df.to_csv(csv_filename, index=False, header=0, encoding='utf-8', )
        # df = pd.read_csv (csv_filename,  encoding='utf8',  header=0,  dtype=str, error_bad_lines=False, )
        df = pd.read_csv (csv_filename,  encoding='utf8',  header=None,  dtype=str, )
        json_filename = dot+str('table_data.json')
        df.to_json (json_filename,)
        json_records = df.reset_index().to_json(orient ='records')

        # print(json_records)
        data = []
        data = json.loads(json_records)
        # print(data)
        json_data = {}

        for entry in data:
            index = entry['index']
            for key, value in entry.items():
                if key != 'index':
                    if key not in json_data:
                        json_data[key] = {}
                    json_data[key][str(index)] = value

        print(json_data)

        
        


        index_horizontal = len(data)
        index_vertical = len(data[0])

        # Initialize dictionaries to hold the split data
        data_keys = list(json_data.keys())
        name_dict = {}
        exp_dict = {}
        location_dict = {}
        technology_dict = {}
        visa_dict = {}
        relocation_dict = {}
        availability_dict = {}

        # Extract data based on keys
        for idx, key in enumerate(data_keys):
            inner_dict = json_data[key]
            
            if "Name" in inner_dict.values():
                name_dict = inner_dict.copy()
            elif "NAME" in inner_dict.values():
                name_dict = inner_dict.copy()
            elif "name" in inner_dict.values():
                name_dict = inner_dict.copy()
            elif "Technology" in inner_dict.values():
                technology_dict = inner_dict.copy()
            elif "Skill" in inner_dict.values():
                technology_dict = inner_dict.copy()
            elif "SKILL SET/TECHNOLOGY" in inner_dict.values():
                technology_dict = inner_dict.copy()
            elif "Job Title" in inner_dict.values():
                technology_dict = inner_dict.copy()
            elif "JOB ROLE" in inner_dict.values():
                technology_dict = inner_dict.copy()
            elif "Exp" in inner_dict.values():
                exp_dict = inner_dict.copy()
            elif "Experience" in inner_dict.values():
                exp_dict = inner_dict.copy()
            elif "EXPERIENCE" in inner_dict.values():
                exp_dict = inner_dict.copy()
            elif "Work Exp" in inner_dict.values():
                exp_dict = inner_dict.copy()
            elif "YEARS" in inner_dict.values():
                exp_dict = inner_dict.copy()
            elif "Location" in inner_dict.values():
                location_dict = inner_dict.copy()
            elif "Current Location" in inner_dict.values():
                location_dict = inner_dict.copy()
            elif "location" in inner_dict.values():
                location_dict = inner_dict.copy()
            elif "LOCATION" in inner_dict.values():
                location_dict = inner_dict.copy()
            elif "Visa" in inner_dict.values():
                visa_dict = inner_dict.copy()
            elif "VISA" in inner_dict.values():
                visa_dict = inner_dict.copy()
            elif "VISA STATUS" in inner_dict.values():
                visa_dict = inner_dict.copy()
            elif "visa" in inner_dict.values():
                visa_dict = inner_dict.copy()
            elif "Relocation" in inner_dict.values():
                relocation_dict = inner_dict.copy()
            elif "RELOCATION" in inner_dict.values():
                relocation_dict = inner_dict.copy()
            elif "Relocate" in inner_dict.values():
                relocation_dict = inner_dict.copy()
            elif "Availability" in inner_dict.values():
                availability_dict = inner_dict.copy()
            elif "Notice Period" in inner_dict.values():
                availability_dict = inner_dict.copy()

        # Convert data values to lists
        name_values = list(name_dict.values())[1:]
        exp_values = list(exp_dict.values())[1:]
        current_values = list(location_dict.values())[1:]
        technology_values = list(technology_dict.values())[1:]
        relocation_values = list(relocation_dict.values())[1:]
        visa_values = list(visa_dict.values())[1:]
        notice_values = list(availability_dict.values())[1:]

        # Convert values to tuples
        name_tuple = tuple(name_values)
        exp_tuple = tuple(exp_values)
        current_tuple = tuple(current_values)
        technology_tuple = tuple(technology_values)
        relocation_tuple = tuple(relocation_values)
        visa_tuple = tuple(visa_values)
        notice_tuple = tuple(notice_values)

        # Print the extracted data
        print("Name:", name_values)
        print("Exp:", exp_values)
        print("Current Location:", current_values)
        print("Technology:", technology_values)
        print("Relocation:", relocation_values)
        print("Visa:", visa_values)
        print("Notice Period:", notice_values)

        

        print("Name:", name_tuple)
        print("Exp:", exp_tuple)
        print("Current Location:", current_tuple)
        print("Technology:", technology_tuple)
        print("Relocation:", relocation_tuple)
        print("Visa:", visa_tuple)
        print("Notice Period:", notice_tuple)

       


                #benchsales data calling
        object_lead = Custombenchsales.objects.get(id=id)
        emailleadsid = object_lead.id
        print(emailleadsid)
        context = {'d': data, 'object':object, 'emailleadsid':emailleadsid, 'first_name':first_name, 'last_name':last_name, 'email_id':email_id, 'phone_number':phone_number, 'indexhorizontal':index_horizontal, 'indexvertical':index_vertical, 'name_tuple':name_tuple, 'exp_tuple':exp_tuple, 'current_tuple':current_tuple, 'technology_tuple':technology_tuple, 'relocation_tuple':relocation_tuple, 'visa_tuple':visa_tuple, 'notice_tuple':notice_tuple}
        # context = {'d': data, 'object':object, 'emailleadsid':emailleadsid, 'first_name':first_name, 'last_name':last_name, 'email_id':email_id, 'phone_number':phone_number, 'indexhorizontal':index_horizontal, 'indexvertical':index_vertical, 'extracted_data':extracted_data}

        return render(request, 'custombenchsalesedits.html', context)
    # error prvention emty array passng to templates
    except Exception as e:
        # return HttpResponse ('hello')
       #data = [{"0":'',"1":'',"2":''}]
       #data = [{"0":''}]
       data = [{}]
       #context = {'d': data, 'object':object,}
       #benchsales data calling
       object_lead = Custombenchsales.objects.get(id=id)
       emailleadsid = object_lead.id
       print(emailleadsid)

       index_horizontal = len(data)
       index_vertical = len(data[0])
       context = {'d': data, 'object':object, 'emailleadsid':emailleadsid, 'first_name':first_name, 'last_name':last_name, 'email_id':email_id, 'phone_number':phone_number, 'indexhorizontal':index_horizontal, 'indexvertical':index_vertical}
       return render(request, 'custombenchsalesedits.html', context)
    
    

# def custombenchsalesedits(request,id):
#     # if request.method=="GET":

#     # object_bench=Custombench.objects.get(id=id)

   
#     # return render(request,'customemailleadsedits.html',{'object':object,})
#     object_bench=Custombenchsales.objects.get(id=id)
#     #print(object.bsEmail_Bodyhtml)
#     content = object_bench.bsEmail_Bodyhtml
#     # html_content = row[4]
#     html_content = content
#     # soup = BeautifulSoup(html_content, 'html.parser')
#     # table = soup.find('table')  # You may need to modify this to match the specific table you want to extract

#     # if table:
#     #     data = []
#     #     rows = table.find_all('tr')

#     #     for row in rows:
#     #         cols = row.find_all('td')
#     #         cols = [col.text.strip() for col in cols]
#     #         data.append(cols)

#     #     df = pd.DataFrame(data)
#     #     print(data)
#     #     # csv_filename = f'table_data.csv'  # Generate a unique CSV file name for each row
#     #     csv_filename = dot +str('table_data.csv')
#     soup = BeautifulSoup(html_content, 'html.parser')
#     table = soup.find('table')  # You may need to modify this to match the specific table you want to extract

#     if table:
#         data = []

#         for row in table.find_all('tr'):
#             cols = row.find_all('td')
#             cols = [extract_data(col) for col in cols]
#             data.append(cols)

#         df = pd.DataFrame(data)
#         # csv_filename = f'table_data_{idx}.csv'  # Generate a unique CSV file name for each row
#         # df.to_csv(csv_filename, index=False)

#         csv_filename = dot +str('table_data.csv')
#         df.to_csv(csv_filename, index=False,)
#         # df = pd.read_csv (csv_filename,  encoding='utf8',  header=0,  dtype=str, error_bad_lines=False, )
#         df = pd.read_csv (csv_filename,  encoding='utf8',  header=0,  dtype=str,  )
#         json_filename = dot+str('table_data.json')
#         df.to_json (json_filename,)
#         json_records = df.reset_index().to_json(orient ='records')
#         data = []
#         data = json.loads(json_records)
#         #object=Custombench.objects.get(id=id)
#         context = {'d': data,}
#         #context = {'d': data, 'object':object,}
#         return render(request, 'custombenchsalesedits.html', context)
#     # else:
#         # print("Table not found in the HTML content of row", id)
#         # object=Custombench.objects.get(id=id)
#         # return render(request, 'custombenchsalesedits.html', {'object':object,})
   

#     # return HttpResponse("hello world")
#     # return HttpResponse(object.bsEmail_Bodyhtml)
#     # return render(request, 'custombenchsalesedits.html', context)
#     return render(request, 'custombenchsalesedits.html', )

# def custombenchsalesedits(request,id):
#     object=Custombench.objects.get(id=id)
#     return render(request, 'custombenchsalesedits.html', {'object':object,})


# def customemailleadsedits(request,id):
#     object_lead=Customemailleads.objects.get(id=id)
#     content = object_lead.Email_Body
#     # print(content)
#     name_pattern = re.compile(r'From:\s([^<]+)')
#     match = name_pattern.search(content)

#     phone_pattern = re.compile(r'Office:\s(\(\d{3}\)\s\d{3}-\d{4})')
#     phone_match = phone_pattern.search(content)

#     company_pattern = re.compile(r'From:\s[^<]+\s<([^@]+@[^>]+)>')
#     company_match = company_pattern.search(content)
#     address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?)\s+(\d{5})')
#     address_match = address_pattern.search(content)

#                 # address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?),\s+(\d{5})')
#                 # address_match = address_pattern.search(text)

#     legalstatus_pattern = re.compile(r'(H1B|No H1B|Green Card|Citizen|Work Visa|Permanent Resident)', re.IGNORECASE)
#     legalstatus_match = legalstatus_pattern.search(content)

#     mobile_pattern = re.compile(r'Mob:\s(\d+)')
#     mobile_match = mobile_pattern.search(content)

#     first_name = ""
#     last_name = ""
#     email_id = ""
#     description = ""
#     position = ""
#     location = ""
#     duration = ""
#     phone_number = ""
#     company_name = ""
#     address = ""
#     city = ""
#     state = ""
#     zipcode = ""
#     legalstatus = ""
#     mobile_number = ""
#     try:
#         if match:
#             name = match.group(1).strip()
#             first_name, _, last_name = name.partition(" ")
#             email_id = re.search(r'<([^>]+)>', content).group(1)
#                         # Extracting description using regex
#             description_pattern = re.compile(r'Subject:.*?\n\n(.*)', re.DOTALL)
#             match = description_pattern.search(content)

#             if match:
#                 description = match.group(1).strip()
#             else:
#                 description = ""

#             if phone_match:
#                 phone_number = phone_match.group(1).strip()
#             else:
#                 phone_number = ""
#             if company_match:
#                 company_email = company_match.group(1).strip()
#                             # company_name = company_email.split('@')[1].strip()
#                             # Split email based on "@"
#                 domain_part = company_email.split('@')[1]
#                             #  1 means after value of symbol. 0 means before value of symbol.
#                             # Extract the company name and remove leading/trailing spaces
#                 company_name = domain_part.split('.')[0].strip().title()
#                 print(company_name)
#                             # Remove portion after the last dot in the domain
#                             # domain_name = '.'.join(domain_part.split('.')[:-1]).title()
#                             # Check if "Inc" is present in the company name and modify accordingly
                            
#             else:
#                 company_name = ""
#                             # Check if "Inc" is present in the text and extract the company name accordingly
#                             # inc_pattern = re.compile(r'\bInc\b', re.IGNORECASE)
#                             # inc_match = inc_pattern.search(text)
#                             # if inc_match:
#                             #     start_index = inc_match.start()
#                             #     company_name = text[:start_index].strip().title()
#                             # else:
#                             #     company_name = ""

#             if address_match:
#                 address = address_match.group(1).strip()
#                 city = address_match.group(2).strip()
#                 state = address_match.group(3).strip()
#                 zipcode = address_match.group(4).strip()
#             else:
#                 address = ""
#                 city = ""
#                 state = ""
#                 zipcode = ""

#             if legalstatus_match:
#                 legalstatus = legalstatus_match.group(0).strip()
#             else:
#                 legalstatus = ""

#             if mobile_match:
#                 mobile_number = mobile_match.group(1).strip()
#             else:
#                 mobile_number = ""



#                         # Extracting position, location, and duration using regex
#             position_pattern = re.compile(r'Position:\s(.*?)\n')
#             location_pattern = re.compile(r'Location:\s(.*?)\n')
#             duration_pattern = re.compile(r'Duration:\s(.*?)\n')

#             position_match = position_pattern.search(content)
#             location_match = location_pattern.search(content)
#             duration_match = duration_pattern.search(content)

#             position = position_match.group(1).strip() if position_match else ""
#             location = location_match.group(1).strip() if location_match else ""
#             duration = duration_match.group(1).strip() if duration_match else ""
        

#         else:
#             first_name = ""
#             last_name = ""
#             email_id = ""
#             description = ""
#             position = ""
#             location = ""
#             duration = ""
#             phone_number = ""
#             company_name = ""
#             address = ""
#             city = ""
#             state = ""
#             zipcode = ""
#             legalstatus = ""
#             mobile_number = ""

#                     # Output the extracted fields
#     except ValueError:
#         # pass
#         first_name = ""
#         last_name = ""
#         email_id = ""
#         description = ""
#         position = ""
#         location = ""
#         duration = ""
#         phone_number = ""
#         company_name = ""
#         address = ""
#         city = ""
#         state = ""
#         zipcode = ""
#         legalstatus = ""
#         mobile_number = ""

    
#     except:
#         first_name = ""
#         last_name = ""
#         email_id = ""
#         description = ""
#         position = ""
#         location = ""
#         duration = ""
#         phone_number = ""
#         company_name = ""
#         address = ""
#         city = ""
#         state = ""
#         zipcode = ""
#         legalstatus = ""
#         mobile_number = ""

#     print("First Name:", first_name)
#     print("Last Name:", last_name)
#     print("Email ID:", email_id)
#     print("Description:", description)
#     print("Position:", position)
#     print("Location:", location)
#     print("Duration:", duration)
#     print("Phone Number:", phone_number)
#     print("Company:", company_name)
#     print("Address:", address)
#     print("City:", city)
#     print("State:", state)
#     print("Zipcode:", zipcode)
#     print("Legalstatus:", legalstatus)
#     print("Mobile Number:", mobile_number)
#     context = {'first_name':first_name,'last_name':last_name, 'email_id':email_id, 'username':first_name+' '+last_name, 'description':description, 'position':position, 'location':location, 'duration':duration, 'phone_number':phone_number, 'company_name':company_name, 'address':address, 'city':city, 'state':state, 'zipcode':zipcode, 'legalstatus':legalstatus, 'mobile_number':mobile_number, }


   
#     return render(request,'customemailleadsedits.html', context)
import re

# def customemailleadsedits(request, id):
#     object_lead = Customemailleads.objects.get(id=id)
#     content = object_lead.Email_Body

#     # name_pattern = re.compile(r'From:\s([^<]+)')
#     name_pattern = re.compile(r'From:\s([^<]+)\s<([^@]+@[^>]+)>')

#     match = name_pattern.search(content)

#     phone_pattern = re.compile(r'Office:\s\((\d{3})\)\s(\d{3})-(\d{4})')
#     phone_match = phone_pattern.search(content)

#     company_pattern = re.compile(r'From:\s[^<]+\s<([^@]+@[^>]+)>')
#     company_match = company_pattern.search(content)

#     address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?)\s+(\d{5})')
#     address_match = address_pattern.search(content)

#     legalstatus_pattern = re.compile(r'(H1B|No H1B|Green Card|Citizen|Work Visa|Permanent Resident)', re.IGNORECASE)
#     legalstatus_match = legalstatus_pattern.search(content)

#     mobile_pattern = re.compile(r'Mob:\s(\d+)')
#     mobile_match = mobile_pattern.search(content)


#     description_pattern = re.compile(r'Subject:.*?\n\n(.*)', re.DOTALL)
#     description_match = description_pattern.search(content)

#     first_name = ""
#     last_name = ""
#     email_id = ""
#     description = ""
#     position = ""
#     location = ""
#     duration = ""
#     phone_number = ""
#     company_name = ""
#     address = ""
#     city = ""
#     state = ""
#     zipcode = ""
#     legalstatus = ""
#     mobile_number = ""

#     try:
#         if match:
#             name = match.group(1).strip()
#             first_name, _, last_name = name.partition(" ")
#             email_id = re.search(r'<([^>]+)>', content).group(1)

#         if phone_match:
#             phone_number = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"

#         # if company_match:
#         #     company_email = company_match.group(1).strip()
#         #     domain_part = company_email.split('@')[1]
#         #     company_name = domain_part.split('.')[0].strip().title()
#         #     if company_name == 'Gmail' or company_name =='Yahoo':
#         #         company_name =''
#         if company_match:
#             company_email = company_match.group(1).strip()
#             domain_part = company_email.split('@')[1]
#             company_name = domain_part.split('.')[0].strip().title()
#             if company_name == 'Gmail' or company_name =='Yahoo':
#                 company_name =''

#             else:
#                 company_name =''

#         # Finding the line that contains the company name
#         company_line = None
#         lines = content.split('\n')
#         for line in lines:
#             if ". |" in line:
#                 company_line = line
#                 break

#         if company_line:
#             # Splitting the line by ". |" and taking the first part to get the company name
#             company_name = company_line.split('. |')[0].strip()
#             # print(company_name)
#         else:
#             company_name =''

#         if address_match:
#             address = address_match.group(1).strip()
#             city = address_match.group(2).strip()
#             state = address_match.group(3).strip()
#             zipcode = address_match.group(4).strip()


#         if description_match:
#             # description = description_match.group(1).strip()
#             description1 = description_match.group(1).strip()
#             patterns = [
#                         r'Sincerely,[\s\S]*?(?=Sincerely,|$)',
#                         r'Sincerely[\s\S]*?(?=Sincerely|$)',
#                         r'Thanks,[\s\S]*?(?=Thanks,|$)',
#                         r'Thanks[\s\S]*?(?=Thanks|$)',
#                         r'Regards[\s\S]*?(?=Regards|$)',
#                         r'Regards,[\s\S]*?(?=Regards,|$)',
#                         r'Thanks & Regards[\s\S]*?(?=Thanks & Regards|$)'
#                         r'Thanks & Regards,[\s\S]*?(?=Thanks & Regards,|$)'
#                     ]
#             combined_pattern = '|'.join(patterns)
#             description = re.sub(combined_pattern, '', description1, flags=re.IGNORECASE)
#             # If none of the patterns matched, assign an empty string to 'description'
#             if description1 == description:
#                 print('ok')
#                 description = description_match.group(1).strip()
#             # else:
#             #     description = ""

    
#         else:
#             description = ""


#         if legalstatus_match:
#             legalstatus = legalstatus_match.group(0).strip()

#         # Extracting position, location, and duration using regex
#         position_pattern = re.compile(r'Position:\s(.*?)\n')
#         location_pattern = re.compile(r'Location:\s(.*?)\n')
#         duration_pattern = re.compile(r'Duration:\s(.*?)\n')

#         position_match = position_pattern.search(content)
#         location_match = location_pattern.search(content)
#         duration_match = duration_pattern.search(content)

#         position = position_match.group(1).strip() if position_match else ""
#         location = location_match.group(1).strip() if location_match else ""
#         duration = duration_match.group(1).strip() if duration_match else "Contract"  # Set default duration if not found

#     except Exception as e:
#         # Handle exceptions if needed
#         pass

#     # Handling mobile number separately to avoid breaking the entire extraction process
#     try:
#         if mobile_match:
#             mobile_number = mobile_match.group(1).strip()
#     except Exception as e:
#         # Handle exceptions if needed
#         pass

#     # Output the extracted fields
#     # print("First Name:", first_name)
#     # print("Last Name:", last_name)
#     # print("Email ID:", email_id)
#     # print("Description:", description)
#     # print("Position:", position)
#     # print("Location:", location)
#     # print("Duration:", duration)
#     # print("Phone Number:", phone_number)
#     # print("Company:", company_name)
#     # print("Address:", address)
#     # print("City:", city)
#     # print("State:", state)
#     # print("Zipcode:", zipcode)
#     # print("Legalstatus:", legalstatus)
#     # print("Mobile Number:", mobile_number)

#     # Create the context dictionary for rendering the template
#     context = {
#         'first_name': first_name,
#         'last_name': last_name,
#         'email_id': email_id,
#         'username': f"{first_name} {last_name}",
#         'description': description,
#         'position': position,
#         'location': location,
#         'duration': duration,
#         'phone_number': phone_number,
#         'company_name': company_name,
#         'address': address,
#         'city': city,
#         'state': state,
#         'zipcode': zipcode,
#         'legalstatus': legalstatus,
#         'mobile_number': mobile_number,
#     }

#     return render(request, 'customemailleadsedits.html', context)



def customemailleadsedits(request, id):
    object_lead = Customemailleads.objects.get(id=id)
    content = object_lead.Email_Body
    emailleadsid = object_lead.id
    #print(emailleadsid)
    #Whatsapp api dropdowns
    # job_type = "https://career.desss.com/dynamic/careerdesssapi.php?action=job"
    # response = requests.get(job_type)
    # job_data = response.json()

    # Extract "name" values from the API response
    # work_type_options = [item["name"] for item in job_data["data"]]

    # workplace = "https://career.desss.com/dynamic/careerdesssapi.php?action=workplace_type"
    # response = requests.get(workplace)
    # job_data = response.json()

    # Extract "name" values from the API response
    # workplace_options = [item["name"] for item in job_data["data"]]
    #duration
    # duration = "https://career.desss.com/dynamic/careerdesssapi.php?action=duration"
    # durationresponse = requests.get(duration)
    # durationjob_data = durationresponse.json()
    # try:
    #    # Extract "name" values from the API response
    #    duration_options = [item["name"] for item in durationjob_data["data"]]
    # except:
    #     duration_options = ''
    #duration
    # legal_status = "https://career.desss.com/dynamic/careerdesssapi.php?action=legal_status"
    # legal_statusresponse = requests.get(legal_status)
    # legal_statusjob_data = legal_statusresponse.json()
    # try:
    #    # Extract "name" values from the API response
    #    legal_status_options = [item["name"] for item in legal_statusjob_data["data"]]
    # except:
    #     legal_status_options = ''
    # #duration
    # remote = "https://career.desss.com/dynamic/careerdesssapi.php?action=remote"
    # remoteresponse = requests.get(remote)
    # remotejob_data = remoteresponse.json()
    # try:
    #    # Extract "name" values from the API response
    #    remote_options = [item["name"] for item in remotejob_data["data"]]
    # except:
    #     remote_options = ''
    # #duration
    # interview_type = "https://career.desss.com/dynamic/careerdesssapi.php?action=interview_type"
    # interview_typeresponse = requests.get(interview_type)
    # interview_typejob_data = interview_typeresponse.json()
    # try:
    #    # Extract "name" values from the API response
    #    interview_type_options = [item["name"] for item in interview_typejob_data["data"]]
    # except:
    #     interview_type_options = ''
    # name_pattern = re.compile(r'From:\s([^<]+)')
    name_pattern = re.compile(r'From:\s([^<]+)\s<([^@]+@[^>]+)>')

    match = name_pattern.search(content)

    phone_pattern = re.compile(r'Office:\s\((\d{3})\)\s(\d{3})-(\d{4})')
    phone_match = phone_pattern.search(content)

    company_pattern = re.compile(r'From:\s[^<]+\s<([^@]+@[^>]+)>')
    company_match = company_pattern.search(content)

    address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?)\s+(\d{5})')
    address_match = address_pattern.search(content)

    legalstatus_pattern = re.compile(r'(H1B|No H1B|Green Card|Citizen|Work Visa|Permanent Resident)', re.IGNORECASE)
    legalstatus_match = legalstatus_pattern.search(content)

    mobile_pattern = re.compile(r'Mob:\s(\d+)')
    mobile_match = mobile_pattern.search(content)


    description_pattern = re.compile(r'Subject:.*?\n\n(.*)', re.DOTALL)
    description_match = description_pattern.search(content)

    # Read skills from CSV
    skills_to_extract = []
    with open(dot+'skills.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            skills_to_extract.append(row['skill'])

    # Create a pattern to match the skills
    pattern_template = r'\b(?:' + '|'.join(re.escape(skill) for skill in skills_to_extract) + r')\b'
    skill_pattern = re.compile(pattern_template, re.IGNORECASE)

    # Find all skills in the email content
    skills_found = skill_pattern.findall(content)

    # Remove duplicates
    unique_skills = list(set(skills_found))

    # Ensure there are 5 skill fields, filling with blanks if needed
    output_skills = unique_skills + [''] * (5 - len(unique_skills))

    # Print the extracted skills
    print("Extracted skills:")
    a = []

    for i, skill in enumerate(output_skills, start=1):
        a.append(skill)
      

    eskill = tuple(a)
    print(eskill)
    print(eskill[0])
    

    first_name = ""
    last_name = ""
    email_id = ""
    description = ""
    position = ""
    location = ""
    duration = ""
    phone_number = ""
    company_name = ""
    address = ""
    city = ""
    state = ""
    zipcode = ""
    legalstatus = ""
    mobile_number = ""
    workplace_value = ""
    job_type_value = ""
    try:
        if match:
            name = match.group(1).strip()
            first_name, _, last_name = name.partition(" ")
            email_id = re.search(r'<([^>]+)>', content).group(1)

        if phone_match:
            phone_number = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"

        # if company_match:
        #     company_email = company_match.group(1).strip()
        #     domain_part = company_email.split('@')[1]
        #     company_name = domain_part.split('.')[0].strip().title()
        #     if company_name == 'Gmail' or company_name =='Yahoo':
        #         company_name =''
        if company_match:
            company_email = company_match.group(1).strip()
            domain_part = company_email.split('@')[1]
            company_name = domain_part.split('.')[0].strip().title()
            if company_name == 'Gmail' or company_name =='Yahoo':
                company_name =''

            else:
                company_name =''

        # Finding the line that contains the company name
        company_line = None
        lines = content.split('\n')
        for line in lines:
            if ". |" in line:
                company_line = line
                break

        if company_line:
            # Splitting the line by ". |" and taking the first part to get the company name
            company_name = company_line.split('. |')[0].strip()
            # print(company_name)
        else:
            company_name =''

        if address_match:
            address = address_match.group(1).strip()
            city = address_match.group(2).strip()
            state = address_match.group(3).strip()
            zipcode = address_match.group(4).strip()


        if description_match:
            # description = description_match.group(1).strip()
            description1 = description_match.group(1).strip()
            patterns = [
                        r'Sincerely,[\s\S]*?(?=Sincerely,|$)',
                        r'Sincerely[\s\S]*?(?=Sincerely|$)',
                        r'Thanks,[\s\S]*?(?=Thanks,|$)',
                        r'Thanks[\s\S]*?(?=Thanks|$)',
                        r'Regards[\s\S]*?(?=Regards|$)',
                        r'Regards,[\s\S]*?(?=Regards,|$)',
                        r'Thanks & Regards[\s\S]*?(?=Thanks & Regards|$)'
                        r'Thanks & Regards,[\s\S]*?(?=Thanks & Regards,|$)'
                    ]
            combined_pattern = '|'.join(patterns)
            description = re.sub(combined_pattern, '', description1, flags=re.IGNORECASE)
            # If none of the patterns matched, assign an empty string to 'description'
            if description1 == description:
                print('ok')
                description = description_match.group(1).strip()
            # else:
            #     description = ""

    
        else:
            description = ""


        if legalstatus_match:
            legalstatus = legalstatus_match.group(0).strip()

        # Extracting position, location, and duration using regex
        position_pattern = re.compile(r'Position:\s(.*?)\n')
        location_pattern = re.compile(r'Location:\s(.*?)\n')
        duration_pattern = re.compile(r'Duration:\s(.*?)\n')

        position_match = position_pattern.search(content)
        location_match = location_pattern.search(content)
        duration_match = duration_pattern.search(content)

        position = position_match.group(1).strip() if position_match else ""
        location = location_match.group(1).strip() if location_match else ""
        duration = duration_match.group(1).strip() if duration_match else "Contract"  # Set default duration if not found

    except Exception as e:
        # Handle exceptions if needed
        pass

    # Handling mobile number separately to avoid breaking the entire extraction process
    try:
        if mobile_match:
            mobile_number = mobile_match.group(1).strip()
    except Exception as e:
        # Handle exceptions if needed
        pass

    workplace_pattern = re.compile(r'(On-site|Hybrid|Remote)', re.IGNORECASE)
    workplace_match = workplace_pattern.search(content)

    if workplace_match:
        workplace_value = workplace_match.group(0).strip()
    else:
        workplace_value =''

    # job_type_value = ""
    job_type_pattern = re.compile(r'(Full-time|Part-time|Contract|Temporary|Other|Volunteer|Internship)', re.IGNORECASE)
    job_type_match = job_type_pattern.search(content)

    if job_type_match:
        job_type_value = job_type_match.group(0).strip()
    else:
        job_type_value =''

    # Output the extracted fields
    # print("First Name:", first_name)
    # print("Last Name:", last_name)
    # print("Email ID:", email_id)
    # print("Description:", description)
    # print("Position:", position)
    # print("Location:", location)
    # print("Duration:", duration)
    # print("Phone Number:", phone_number)
    # print("Company:", company_name)
    # print("Address:", address)
    # print("City:", city)
    # print("State:", state)
    # print("Zipcode:", zipcode)
    # print("Legalstatus:", legalstatus)
    # print("Mobile Number:", mobile_number)
    # PHP data Processing
    try:
        url = 'https://career.desss.com/dynamic/careerdesssapi.php?action=check_employer_lead'
    except:
        print('error occured PHP data processing')
    email = email_id
    #demonstrate how to use the 'params' parameter:
    phpdata = requests.get(url, params = {"email": email})
    php_data = phpdata.json()
    php_code = phpdata.status_code
    print(php_data)
    print(php_code)
    if int(php_code)==200:
        first_name = php_data['data']['first_name']
        last_name = php_data['data']['last_name']
        email_id = php_data['data']['email']
        username = php_data['data']['usrename']
        company_name = php_data['data']['company']
        address = php_data['data']['address']
        address2 = php_data['data']['address2']
        phone_number = php_data['data']['phone']
        # location = php_data['data']['email']
        # street = php_data['data']['email']
        city = php_data['data']['city']
        state = php_data['data']['state']
        zipcode = php_data['data']['zip_code']
        # legal_status =php_data['data']['email']
        # mobile_number = php_data['data']['email']
        
        context = {
            'first_name': first_name,
            'last_name': last_name,
            'email_id': email_id,
            'username': username,
            'description': description,
            'position': position,
            'location': location,
            'duration': duration,
            'phone_number': phone_number,
            'company_name': company_name,
            'address': address,
            'address2': address2,
            'city': city,
            'state': state,
            'zipcode': zipcode,
            'legalstatus': legalstatus,
            'mobile_number': mobile_number,
            'skill1': eskill[0],
            'skill2': eskill[1],
            'skill3': eskill[2],
            'skill4': eskill[3],
            'skill5': eskill[4],
            'emailleadsid':emailleadsid,
            # 'work_type_options': work_type_options,
            # 'workplace_options': workplace_options,
            # "duration_options": duration_options,
            # "legal_status_options": legal_status_options,
            # "remote_options": remote_options,
            # "interview_type_options": interview_type_options,
            'is_status_check': 'This email id is exist in the Career site',
            'workplace_value': workplace_value,
            'job_type_value':job_type_value,
        }

        
    elif int(php_code)==400:
        print('error')
        context = {
        'first_name': first_name,
        'last_name': last_name,
        'email_id': email_id,
        'username': f"{first_name} {last_name}",
        'description': description,
        'position': position,
        'location': location,
        'duration': duration,
        'phone_number': phone_number,
        'company_name': company_name,
        'address': address,
        'city': city,
        'state': state,
        'zipcode': zipcode,
        'legalstatus': legalstatus,
        'mobile_number': mobile_number,
        'skill1': eskill[0],
        'skill2': eskill[1],
        'skill3': eskill[2],
        'skill4': eskill[3],
        'skill5': eskill[4],
        'emailleadsid':emailleadsid,
        # 'work_type_options': work_type_options,
        # 'workplace_options': workplace_options,
        # "duration_options": duration_options,
        # "legal_status_options": legal_status_options,
        # "remote_options": remote_options,
        # "interview_type_options": interview_type_options,
        'is_status_check': 'This email id is not exist in the Career site',
         'workplace_value': workplace_value,
        'job_type_value':job_type_value,
       }
    else:
        print('server error')

    # extracted_data = extract_information(content)

       


    # Create the context dictionary for rendering the template
        context = {
            'first_name': first_name,
            'last_name': last_name,
            'email_id': email_id,
            'username': f"{first_name} {last_name}",
            'description': description,
            'position': position,
            'location': location,
            'duration': duration,
            'phone_number': phone_number,
            'company_name': company_name,
            'address': address,
            'city': city,
            'state': state,
            'zipcode': zipcode,
            'legalstatus': legalstatus,
            'mobile_number': mobile_number,
            'skill1': eskill[0],
            'skill2': eskill[1],
            'skill3': eskill[2],
            'skill4': eskill[3],
            'skill5': eskill[4],
            'emailleadsid':emailleadsid,
            # 'work_type_options': work_type_options,
            # 'workplace_options': workplace_options,
            # "duration_options": duration_options,
            # "legal_status_options": legal_status_options,
            # "remote_options": remote_options,
            # "interview_type_options": interview_type_options,
            'is_status_check': 'This email id is not exist in the Career site',
             'workplace_value': workplace_value,
            'job_type_value':job_type_value,
        }

    return render(request, 'customemailleadsedits.html', context)

# Whatsup career sales

class whatsappcareersales_view(View):
    
    def get(self,  request):
        
        details = Film.objects.filter(dropdownlist='Careersales').order_by('id')

        page_number = request.GET.get('page', 1)
       
        # Create a Paginator object with your queryset and the number of items per page
        paginator = Paginator(details, 25)  # Change '10' to the number of items you want per page

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

        return render(request, 'whatsappcareersales.html', context)
      

    def post(self, request, *args, **kwargs):
      
         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')
            # if product_ids == product_ids:
            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:
                    # product = Film.object.get(pk=id)
                    obj = get_object_or_404(Film, id = id)
                    obj.delete()
                return redirect('home')
            elif 'ids[]' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(snippet_ids)
                for id in snippet_ids:
             
                    print(id)
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                return redirect('whatsupcareersales')
            elif 'id' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(delete_idd)
              
                id = delete_idd
                obj = get_object_or_404(Film, id=id)
                obj.delete()
                
                return redirect('whatsupcareersales')
            else:
                return redirect('whatsupcareersales')



def whatsappcareersalesview(request,id):
    object=Film.objects.get(id=id)
    # details = Film.objects.filter(dropdownlist='Careersales').get(id=id)

   
    return render(request,'whatsappcareersalesview.html',{'object':object,})


# def email_splitter(email):
#     username = email.split('@')[0]
#     domain = email.split('@')[1]
#     domain_name = domain.split('.')[0]
#     domain_type = domain.split('.')[1]

#     print('Username : ', username)
#     print('Domain   : ', domain_name)
#     print('Type     : ', domain_type)
#     return username


# def whatsappcareersalesedit(request, id):
#     object_lead = Film.objects.get(id=id)
#     content = object_lead.filmurl
    
#     # Read skills from CSV
#     skills_to_extract = []
#     with open(dot+'skills.csv', 'r') as csv_file:
#         csv_reader = csv.DictReader(csv_file)
#         for row in csv_reader:
#             skills_to_extract.append(row['skill'])

#     # Create a pattern to match the skills
#     pattern_template = r'\b(?:' + '|'.join(re.escape(skill) for skill in skills_to_extract) + r')\b'
#     skill_pattern = re.compile(pattern_template, re.IGNORECASE)

#     # Find all skills in the email content
#     skills_found = skill_pattern.findall(content)

#     # Remove duplicates
#     unique_skills = list(set(skills_found))

#     # Ensure there are 5 skill fields, filling with blanks if needed
#     output_skills = unique_skills + [''] * (5 - len(unique_skills))

#     # Print the extracted skills
#     print("Extracted skills:")
#     a = []

#     for i, skill in enumerate(output_skills, start=1):
#         a.append(skill)
      

#     eskill = tuple(a)
#     print(eskill)
#     print(eskill[0])
#     #Whatsapp api dropdowns
#     job_type = "https://career.desss.com/dynamic/careerdesssapi.php?action=job"
#     response = requests.get(job_type)
#     job_data = response.json()
#     try:
#         # Extract "name" values from the API response
#         work_type_options = [item["name"] for item in job_data["data"]]
#     except:
#         work_type_options = ''

#     workplace = "https://career.desss.com/dynamic/careerdesssapi.php?action=workplace_type"
#     response = requests.get(workplace)
#     job_data = response.json()
#     try:
#        # Extract "name" values from the API response
#        workplace_options = [item["name"] for item in job_data["data"]]
#     except:
#         workplace_options = ''
        
#     # Email ID extraction
#     email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
#     email_match = email_pattern.search(content)
#     email_id = email_match.group() if email_match else ''

#     # Phone number extraction for multiple country formats
#     # phone_pattern = re.compile(r'(?:\+1\s?)??[-.\s]?\d{3}[-.\s]?\d{4}|(?:\+44\s?)?)?\s?\d{4}[-.\s]?\d{6}|(?:\+91\s?)?\d{10}')
#     # phone_match = phone_pattern.search(content)
#     # phone_number = phone_match.group() if phone_match else ''
#     phone_pattern = re.compile(r'(?:\+1\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|(?:\+44\s?)?\(?(?:0\))?\s?\d{4}[-.\s]?\d{6}|(?:\+91\s?)?\d{10}')
#     phone_match = phone_pattern.search(content)
#     phone_number = phone_match.group() if phone_match else ''

#     # Address extraction
#     address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?)\s+(\d{5})')
#     address_match = address_pattern.search(content)
#     street = address_match.group(1) if address_match else ''
#     # city = address_match.group(2) if address_match else ''
#     # state = address_match.group(3) if address_match else ''
#     zip_code = address_match.group(4) if address_match else ''

#     # Legal status extraction
#     legalstatus_pattern = re.compile(r'(?i)\b(H1B|No H1B|No H1-B|Green Card|Citizen|Work Visa|Permanent Resident|GC|USC|OPT|CPT)\b')
#     legalstatus_match = legalstatus_pattern.search(content)
#     legal_status = legalstatus_match.group(1) if legalstatus_match else ''

#     # Mobile number extraction
#     mobile_pattern = re.compile(r'Mob:\s(\d+)')
#     mobile_match = mobile_pattern.search(content)
#     mobile_number = mobile_match.group(1) if mobile_match else ''


#     # Location extraction
#     location_pattern = re.compile(r'Location\s*:\s*(.*?)\s*Preferred\s*location', re.IGNORECASE)
#     location_match = location_pattern.search(content)
#     location = location_match.group(1).strip() if location_match else ''

    
#     # Load spaCy English language model
#     nlp = spacy.load("en_core_web_sm")

#     # Process the text with spaCy
#     doc = nlp(content)

#     # Extract city and state entities
#     cities = []
#     states = []
#     us_states = {
#     "Alabama": "AL",
#     "Alaska": "AK",
#     "Arizona": "AZ",
#     "Arkansas": "AR",
#     "California": "CA",
#     "Colorado": "CO",
#     "Connecticut": "CT",
#     "Delaware": "DE",
#     "Florida": "FL",
#     "Georgia": "GA",
#     "Hawaii": "HI",
#     "Idaho": "ID",
#     "Illinois": "IL",
#     "Indiana": "IN",
#     "Iowa": "IA",
#     "Kansas": "KS",
#     "Kentucky": "KY",
#     "Louisiana": "LA",
#     "Maine": "ME",
#     "Maryland": "MD",
#     "Massachusetts": "MA",
#     "Michigan": "MI",
#     "Minnesota": "MN",
#     "Mississippi": "MS",
#     "Missouri": "MO",
#     "Montana": "MT",
#     "Nebraska": "NE",
#     "Nevada": "NV",
#     "New Hampshire": "NH",
#     "New Jersey": "NJ",
#     "New Mexico": "NM",
#     "New York": "NY",
#     "North Carolina": "NC",
#     "North Dakota": "ND",
#     "Ohio": "OH",
#     "Oklahoma": "OK",
#     "Oregon": "OR",
#     "Pennsylvania": "PA",
#     "Rhode Island": "RI",
#     "South Carolina": "SC",
#     "South Dakota": "SD",
#     "Tennessee": "TN",
#     "Texas": "TX",
#     "Utah": "UT",
#     "Vermont": "VT",
#     "Virginia": "VA",
#     "Washington": "WA",
#     "West Virginia": "WV",
#     "Wisconsin": "WI",
#     "Wyoming": "WY"}

#     us_cities = [
#     "New York", "Los Angeles", "Chicago", "Houston", "Philadelphia",
#     "Phoenix", "San Antonio", "San Diego", "Dallas", "San Jose",
#     "Jacksonville", "Indianapolis", "Austin", "San Francisco", "Columbus",
#     "Fort Worth", "Charlotte", "Detroit", "El Paso", "Memphis",
#     "Seattle", "Denver", "Washington", "Boston", "Nashville",
#     "Baltimore", "Oklahoma City", "Louisville", "Portland", "Las Vegas",
#     "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Sacramento",
#     "Kansas City", "Long Beach", "Mesa", "Atlanta", "Colorado Springs",]
#     # ... Add more cities]


#     for ent in doc.ents:
#         if ent.label_ == "GPE":  # GPE label in spaCy represents geopolitical entities
#             if ent.text in us_cities:
#                 cities.append(ent.text)
#             elif ent.text in us_states or ent.text in us_states.values():
#                 states.append(ent.text)

#     # Print extracted cities and states
#     # print("Cities:", cities)
#     # print("States:", states)
#     city = ','.join(cities)
#     state = ','.join(states)
#     # if int(len(email_id)) != 0:
       
        
#     #     # Now lets find the location of the "@" sign
#     #     index = email_id.index("@")

#     #     # Next lets get the string starting from the begining up to the location of the "@" sign.
#     #     name = email_id[:index]
#     #     # print(name)
#     # else:
#     #     name = ''
    
#     # Extract the name using regex
#     name_pattern = re.compile(r'^([^@]+)')
#     name_match = name_pattern.search(email_id)

#     if name_match:
#         first_name = name_match.group(1)
#         print("Extracted name:", first_name)
#     else:
#         print("Name not found in the email address.")
#         first_name = ''

#     # Create a dictionary to store the extracted information
#     extracted_data = {
#         "first_name": first_name,
#         "email_id": email_id,
#         "phone_number": phone_number,
#         "Location:": location,
#         "street": street,
#         "city": city,
#         "state": state,
#         "zip_code": zip_code,
#         "legal_status": legal_status,
#         "mobile_number": mobile_number,
#         "object_lead":object_lead,
#         "work_type_options": work_type_options,
#         "workplace_options": workplace_options,
#         'skill1': eskill[0],
#         'skill2': eskill[1],
#         'skill3': eskill[2],
#         'skill4': eskill[3],
#         'skill5': eskill[4],

#     }

#     # Now you can use the extracted_data dictionary as needed, such as storing it in a database or processing it further.
#     print(extracted_data)
   

#     # return render(request, 'whatsappcareersalesedit.html', {'object_lead':object_lead})

#     return render(request, 'whatsappcareersalesedit.html', extracted_data)


def extract_information(content, id):
    object_lead = Film.objects.get(id=id)
    content = object_lead.filmurl
    
    # Read skills from CSV
    skills_to_extract = []
    with open(dot+'skills.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            skills_to_extract.append(row['skill'])

    # Create a pattern to match the skills
    pattern_template = r'\b(?:' + '|'.join(re.escape(skill) for skill in skills_to_extract) + r')\b'
    skill_pattern = re.compile(pattern_template, re.IGNORECASE)

    # Find all skills in the email content
    skills_found = skill_pattern.findall(content)

    # Remove duplicates
    unique_skills = list(set(skills_found))

    # Ensure there are 5 skill fields, filling with blanks if needed
    output_skills = unique_skills + [''] * (5 - len(unique_skills))

    # Print the extracted skills
    print("Extracted skills:")
    a = []

    for i, skill in enumerate(output_skills, start=1):
        a.append(skill)
      

    eskill = tuple(a)
    print(eskill)
    print(eskill[0])
    #Whatsapp api dropdowns
    # job_type = "https://career.desss.com/dynamic/careerdesssapi.php?action=job"
    # response = requests.get(job_type)
    # job_data = response.json()
    # try:
    #     # Extract "name" values from the API response
    #     work_type_options = [item["name"] for item in job_data["data"]]
    # except:
    #     work_type_options = ''

    # workplace = "https://career.desss.com/dynamic/careerdesssapi.php?action=workplace_type"
    # response = requests.get(workplace)
    # job_data = response.json()
    # try:
    #    # Extract "name" values from the API response
    #    workplace_options = [item["name"] for item in job_data["data"]]
    # except:
    #     workplace_options = ''
        
    # Email ID extraction
    email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
    email_match = email_pattern.search(content)
    email_id = email_match.group() if email_match else ''

    # Phone number extraction for multiple country formats
    # phone_pattern = re.compile(r'(?:\+1\s?)??[-.\s]?\d{3}[-.\s]?\d{4}|(?:\+44\s?)?)?\s?\d{4}[-.\s]?\d{6}|(?:\+91\s?)?\d{10}')
    # phone_match = phone_pattern.search(content)
    # phone_number = phone_match.group() if phone_match else ''
    phone_pattern = re.compile(r'(?:\+1\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|(?:\+44\s?)?\(?(?:0\))?\s?\d{4}[-.\s]?\d{6}|(?:\+91\s?)?\d{10}')
    phone_match = phone_pattern.search(content)
    phone_number = phone_match.group() if phone_match else ''

    # Address extraction
    address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?)\s+(\d{5})')
    address_match = address_pattern.search(content)
    street = address_match.group(1) if address_match else ''
    # city = address_match.group(2) if address_match else ''
    # state = address_match.group(3) if address_match else ''
    zip_code = address_match.group(4) if address_match else ''

    # Legal status extraction
    legalstatus_pattern = re.compile(r'(?i)\b(H1B|No H1B|No H1-B|Green Card|Citizen|Work Visa|Permanent Resident|GC|USC|OPT|CPT)\b')
    legalstatus_match = legalstatus_pattern.search(content)
    legal_status = legalstatus_match.group(1) if legalstatus_match else ''

    # Mobile number extraction
    mobile_pattern = re.compile(r'Mob:\s(\d+)')
    mobile_match = mobile_pattern.search(content)
    mobile_number = mobile_match.group(1) if mobile_match else ''


    # Location extraction
    location_pattern = re.compile(r'Location\s*:\s*(.*?)\s*Preferred\s*location', re.IGNORECASE)
    location_match = location_pattern.search(content)
    location = location_match.group(1).strip() if location_match else ''

    
    # Load spaCy English language model
    nlp = spacy.load("en_core_web_sm")

    # Process the text with spaCy
    doc = nlp(content)

    # Extract city and state entities
    cities = []
    states = []
    us_states = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY"}

    us_cities = [
    "New York", "Los Angeles", "Chicago", "Houston", "Philadelphia",
    "Phoenix", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Jacksonville", "Indianapolis", "Austin", "San Francisco", "Columbus",
    "Fort Worth", "Charlotte", "Detroit", "El Paso", "Memphis",
    "Seattle", "Denver", "Washington", "Boston", "Nashville",
    "Baltimore", "Oklahoma City", "Louisville", "Portland", "Las Vegas",
    "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Sacramento",
    "Kansas City", "Long Beach", "Mesa", "Atlanta", "Colorado Springs",]
    # ... Add more cities]


    for ent in doc.ents:
        if ent.label_ == "GPE":  # GPE label in spaCy represents geopolitical entities
            if ent.text in us_cities:
                cities.append(ent.text)
            elif ent.text in us_states or ent.text in us_states.values():
                states.append(ent.text)

    # Print extracted cities and states
    # print("Cities:", cities)
    # print("States:", states)
    city = ','.join(cities)
    state = ','.join(states)
    # if int(len(email_id)) != 0:
       
        
    #     # Now lets find the location of the "@" sign
    #     index = email_id.index("@")

    #     # Next lets get the string starting from the begining up to the location of the "@" sign.
    #     name = email_id[:index]
    #     # print(name)
    # else:
    #     name = ''
    
    # Extract the name using regex
    name_pattern = re.compile(r'^([^@]+)')
    name_match = name_pattern.search(email_id)

    if name_match:
        first_name = name_match.group(1)
        print("Extracted name:", first_name)
    else:
        print("Name not found in the email address.")
        first_name = ''

    # Create a dictionary to store the extracted information
    extracted_data = {
        "first_name": first_name,
        "email_id": email_id,
        "phone_number": phone_number,
        "Location:": location,
        "street": street,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "legal_status": legal_status,
        "mobile_number": mobile_number,
        # "object_lead":object_lead,
        # "work_type_options": work_type_options,
        # "workplace_options": workplace_options,
        'skill1': eskill[0],
        'skill2': eskill[1],
        'skill3': eskill[2],
        'skill4': eskill[3],
        'skill5': eskill[4],

    }

    # Now you can use the extracted_data dictionary as needed, such as storing it in a database or processing it further.
    print(extracted_data)
   

    # return render(request, 'whatsappcareersalesedit.html', {'object_lead':object_lead})

    # return extracted_data
    return first_name, email_id, phone_number, location, street,city, state, zip_code, legal_status, mobile_number

def whatsappcareersalesedit(request, id):
    object_lead = Film.objects.get(id=id)
    content = object_lead.filmurl
    
    # Read skills from CSV
    skills_to_extract = []
    with open(dot+'skills.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            skills_to_extract.append(row['skill'])

    # Create a pattern to match the skills
    pattern_template = r'\b(?:' + '|'.join(re.escape(skill) for skill in skills_to_extract) + r')\b'
    skill_pattern = re.compile(pattern_template, re.IGNORECASE)

    # Find all skills in the email content
    skills_found = skill_pattern.findall(content)

    # Remove duplicates
    unique_skills = list(set(skills_found))

    # Ensure there are 5 skill fields, filling with blanks if needed
    output_skills = unique_skills + [''] * (5 - len(unique_skills))

    # Print the extracted skills
    print("Extracted skills:")
    a = []

    for i, skill in enumerate(output_skills, start=1):
        a.append(skill)
      

    eskill = tuple(a)
    # print(eskill)
    # print(eskill[0])
    #Whatsapp api dropdowns
    # job_type = "https://career.desss.com/dynamic/careerdesssapi.php?action=job"
    # response = requests.get(job_type)
    # job_data = response.json()
    # try:
    #     # Extract "name" values from the API response
    #     work_type_options = [item["name"] for item in job_data["data"]]
    # except:
    #     work_type_options = ''
    
    # workplace = "https://career.desss.com/dynamic/careerdesssapi.php?action=workplace_type"
    # response = requests.get(workplace)
    # job_data = response.json()
    # try:
    #    # Extract "name" values from the API response
    #    workplace_options = [item["name"] for item in job_data["data"]]
    # except:
    #     workplace_options = ''
    # #duration
    # duration = "https://career.desss.com/dynamic/careerdesssapi.php?action=duration"
    # durationresponse = requests.get(duration)
    # durationjob_data = durationresponse.json()
    # try:
    #    # Extract "name" values from the API response
    #    duration_options = [item["name"] for item in durationjob_data["data"]]
    # except:
    #     duration_options = ''
    # #duration
    # legal_statusurl = "https://career.desss.com/dynamic/careerdesssapi.php?action=legal_status"
    # legal_statusresponse = requests.get(legal_statusurl)
    # legal_statusjob_data = legal_statusresponse.json()
    # try:
    #    # Extract "name" values from the API response
    #    legal_status_options = [item["name"] for item in legal_statusjob_data["data"]]
    # except:
    #     legal_status_options = ''
    # #duration
    # remote = "https://career.desss.com/dynamic/careerdesssapi.php?action=remote"
    # remoteresponse = requests.get(remote)
    # remotejob_data = remoteresponse.json()
    # try:
    #    # Extract "name" values from the API response
    #    remote_options = [item["name"] for item in remotejob_data["data"]]
    # except:
    #     remote_options = ''
    # #duration
    # interview_type = "https://career.desss.com/dynamic/careerdesssapi.php?action=interview_type"
    # interview_typeresponse = requests.get(interview_type)
    # interview_typejob_data = interview_typeresponse.json()
    # try:
    #    # Extract "name" values from the API response
    #    interview_type_options = [item["name"] for item in interview_typejob_data["data"]]
    # except:
    #     interview_type_options = ''
    workplace_value =''
    job_type_value =''
    workplace_pattern = re.compile(r'(On-site|Hybrid|Remote)', re.IGNORECASE)
    workplace_match = workplace_pattern.search(content)

    if workplace_match:
        workplace_value = workplace_match.group(0).strip()
    else:
        workplace_value =''

    # job_type_value = ""
    job_type_pattern = re.compile(r'(Full-time|Part-time|Contract|Temporary|Other|Volunteer|Internship)', re.IGNORECASE)
    job_type_match = job_type_pattern.search(content)

    if job_type_match:
        job_type_value = job_type_match.group(0).strip()
    else:
        job_type_value =''
    #php data processing
    email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
    email_match = email_pattern.search(content)
    email_id = email_match.group() if email_match else ''
    email = email_id
    # Legal status extraction
    legalstatus_pattern = re.compile(r'(?i)\b(H1B|No H1B|No H1-B|Green Card|Citizen|Work Visa|Permanent Resident|GC|USC|OPT|CPT)\b')
    legalstatus_match = legalstatus_pattern.search(content)
    legal_status = legalstatus_match.group(1) if legalstatus_match else ''
    try:
        url = 'https://career.desss.com/dynamic/careerdesssapi.php?action=check_employer_lead'
    except:
        print('Invalid url in PHP')

    #demonstrate how to use the 'params' parameter:
    phpdata = requests.get(url, params = {"email": email})
    php_data = phpdata.json()
    php_code = phpdata.status_code
    print(php_data)
    print(php_code)
    if int(php_code)==200:
        first_name = php_data['data']['first_name']
        last_name = php_data['data']['last_name']
        email_id = php_data['data']['email']
        username = php_data['data']['usrename']
        company = php_data['data']['company']
        address = php_data['data']['address']
        address2 = php_data['data']['address2']
        phone_number = php_data['data']['phone']
        # location = php_data['data']['email']
        # street = php_data['data']['email']
        city = php_data['data']['city']
        state = php_data['data']['state']
        zip_code = php_data['data']['zip_code']
        # legal_status =php_data['data']['email']
        # mobile_number = php_data['data']['email']
        extracted_data = {
        "id":id,
        "first_name": first_name,
        "last_name":last_name,
        "email_id": email_id,
        "username": username,
        "company_name": company,
        "address":address,
        "address2":address2,
        "phone_number": phone_number,
        # "Location:": location,
        # "street": street,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "legal_status": legal_status,
        # "mobile_number": mobile_number,
        "object_lead":object_lead,
        # "work_type_options": work_type_options,
        # "workplace_options": workplace_options,
        # "duration_options": duration_options,
        # "legal_status_options": legal_status_options,
        # "remote_options": remote_options,
        # "interview_type_options": interview_type_options,
        'skill1': eskill[0],
        'skill2': eskill[1],
        'skill3': eskill[2],
        'skill4': eskill[3],
        'skill5': eskill[4],
        'is_status_check': 'This email id is exist in the Career site',
        'workplace_value': workplace_value,
        'job_type_value': job_type_value,

       }
        
    elif int(php_code)==400:
        print('error')
        first_name, email_id, phone_number, location, street,city, state, zip_code, legal_status, mobile_number = extract_information(content, id)
        extracted_data = {
         "id":id,
        "first_name": first_name,
        "email_id": email_id,
        "username": first_name,
        "phone_number": phone_number,
        "Location:": location,
        # "street": street,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "legal_status": legal_status,
        # "mobile_number": mobile_number,
        "object_lead":object_lead,
        # "work_type_options": work_type_options,
        # "workplace_options": workplace_options,
        # "duration_options": duration_options,
        # "legal_status_options": legal_status_options,
        # "remote_options": remote_options,
        # "interview_type_options": interview_type_options,
        'skill1': eskill[0],
        'skill2': eskill[1],
        'skill3': eskill[2],
        'skill4': eskill[3],
        'skill5': eskill[4],
        'is_status_check': 'This email id is not exist in the Career site',
        'workplace_value': workplace_value,
        'job_type_value': job_type_value,
       }
    else:
        print('server error')
        first_name, email_id, phone_number, location, street,city, state, zip_code, legal_status, mobile_number = extract_information(content, id)

    # extracted_data = extract_information(content)
    
    # Create a dictionary to store the extracted information
        extracted_data = {
             "id":id,
            "first_name": first_name,
            "email_id": email_id,
            "username": first_name,
            "phone_number": phone_number,
            "Location:": location,
            # "street": street,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "legal_status": legal_status,
            # "mobile_number": mobile_number,
            "object_lead":object_lead,
            # "work_type_options": work_type_options,
            # "workplace_options": workplace_options,
            # "duration_options": duration_options,
            # "legal_status_options": legal_status_options,
            # "remote_options": remote_options,
            # "interview_type_options": interview_type_options,
            'skill1': eskill[0],
            'skill2': eskill[1],
            'skill3': eskill[2],
            'skill4': eskill[3],
            'skill5': eskill[4],  
           'is_status_check': 'This email id is not exist in the Career site',
           'workplace_value': workplace_value,
           'job_type_value': job_type_value,
        }

    # Now you can use the extracted_data dictionary as needed, such as storing it in a database or processing it further.
    # print(extracted_data)
   

    # return render(request, 'whatsappcareersalesedit.html', {'object_lead':object_lead})

    return render(request, 'whatsappcareersalesedit.html', extracted_data)

def whatsappcareersalescreate(request):
    if request.method=="POST":
        
        if 'chiliadstaffingapi' in request.POST:
            
            leadfirstname=request.POST['leadfirstname']
            leadlastname=request.POST['leadlastname']
            leademail=request.POST['leademail']
            leadusername=request.POST['leadusername']
            leadpassword='Desss@123'
            leadcompany=request.POST['leadcompany']
            leadphonenumber=request.POST['leadphonenumber']
            leadaddress=request.POST['leadaddress']
            leadaddress2=request.POST['leadaddress2']
            leadcity=request.POST['leadcity']
            leadstate=request.POST['leadstate']
            leadzipcode=request.POST['leadzipcode']
            
            leadposition=request.POST['leadposition']
            leaddescription=request.POST['leaddescription']
            leadlocation = request.POST['leadlocation']
            leadduration = request.POST['leadduration']
            leadlegalstatus = request.POST['leadlegalstatus']
            leadinterviewtype = request.POST['leadinterviewtype']
            leadworktype = request.POST['leadworktype']
            leadremote = request.POST['leadremote']
            leadexperience = request.POST['leadexperience']
            leadrate = request.POST['leadrate']
            obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadposition=leadposition,leaddescription=leaddescription,
            leadlocation = leadlocation,leadduration = leadduration, leadlegalstatus = leadlegalstatus,leadinterviewtype = leadinterviewtype,leadworktype = leadworktype,leadremote = leadremote,
            leadexperience = leadexperience,leadrate = leadrate)
            obj.save()
            # print(leademail)
                            
           
            url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
            # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
            response = requests.get(url)
            print(response.text)  # Print the response from the API
    
            if response.status_code == 200:
                        
                            messages.success(request, 'Your lead has been updated to chiliadstaffing.com successfully!')  # Success message
                            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
 
            elif response.status_code == 403:
                        
                            # messages.success(request, 'No update was made. In our database, the data you provided has already been updated!')  # Success message
                            messages.success(request, 'Lead update was made. In our database, the job data you provided has already been updated!')
                            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                messages.error(request, 'Your lead has not been updated to chiliadstaffing.com!')  # Error message
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            return redirect('customemailleads')


                        
        elif 'careerdesssapi' in request.POST:
                leadfirstname=request.POST['leadfirstname']
                leadlastname=request.POST['leadlastname']
                leademail=request.POST['leademail']
                leadusername=request.POST['leadusername']
                leadpassword='Desss@123'
                leadcompany=request.POST['leadcompany']
                leadphonenumber=request.POST['leadphonenumber']
                leadaddress=request.POST['leadaddress']
                leadaddress2=request.POST['leadaddress2']
                leadcity=request.POST['leadcity']
                leadstate=request.POST['leadstate']
                leadzipcode=request.POST['leadzipcode']
                
                leadposition=request.POST['leadposition']
                leaddescription=request.POST['leaddescription']
                leadlocation = request.POST['leadlocation']
                leadduration = request.POST['leadduration']
                leadlegalstatus = request.POST['leadlegalstatus']
                leadinterviewtype = request.POST['leadinterviewtype']
                leadworktype = request.POST['leadworktype']
                leadremote = request.POST['leadremote']
                leadexperience = request.POST['leadexperience']
                leadrate = request.POST['leadrate']
                # new data fields
                leadskills1 = request.POST['leadskills1']
                leadexperience1 = request.POST['leadexperience1']
                leadskills2 = request.POST['leadskills2']
                leadexperience2 = request.POST['leadexperience2']
                leadskills3 = request.POST['leadskills3']
                leadexperience3 = request.POST['leadexperience3']
                leadskills4 = request.POST['leadskills4']
                leadexperience4 = request.POST['leadexperience4']
                leadskills5 = request.POST['leadskills5']
                leadexperience5 = request.POST['leadexperience5']
                emailleadid = request.POST['emailleadid']
                #print(leademail)
                # obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadposition=leadposition,leaddescription=leaddescription,
                # leadlocation = leadlocation,leadduration = leadduration, leadlegalstatus = leadlegalstatus,leadinterviewtype = leadinterviewtype,leadworktype = leadworktype,leadremote = leadremote,
                # leadexperience = leadexperience,leadrate = leadrate,  leadskills1 = leadskills1,leadexperience1 = leadexperience1, leadskills2 = leadskills2,leadexperience2 = leadexperience2, leadskills3 = leadskills3, leadexperience3 = leadexperience3, leadskills4 = leadskills4, leadexperience4 = leadexperience4, leadskills5 =leadskills5,
                # leadexperience5 = leadexperience5,)
                # obj.save()
                # django inbuilt function for removing html tags
                leaddescriptiontext1 = strip_tags(leaddescription).strip()
                leaddescriptiontext  = leaddescriptiontext1.replace("'", "")
               
                print(leadlocation)
                print(leadexperience)
      
                # URL for the API endpoint
                url = "https://career.desss.com/dynamic/careerdesssapi.php?action=employer_lead"

                # Sample data as a dictionary
                data = {
                'firstname':leadfirstname,
                'lastname':leadlastname,
                'email':leademail,
                'username':leadusername,
                'password':leadpassword,
                'company':leadcompany,
                'phonenumber':leadphonenumber,
                'address':leadaddress,
                'address2':leadaddress2,
                'city':leadcity,
                'state':leadstate,
                'zipcode':leadzipcode,
                'occupation':leadposition,
                'description':leaddescriptiontext,
                'leadlocation':leadlocation,
                'leadduration':leadduration,
                'leadlegalstatus':leadlegalstatus,
                'leadinterviewtype':leadinterviewtype,
                'leadworktype':leadworktype,
                'leadremote':leadremote,
                'leadexperience':leadexperience,
                'leadrate':leadrate,
                'leadskills1' : leadskills1,
                'leadexperience1' : leadexperience1,
                'leadskills2' : leadskills2,
                'leadexperience2' : leadexperience2,
                'leadskills3' : leadskills3,
                'leadexperience3' : leadexperience3,
                'leadskills4' : leadskills4,
                'leadexperience4' : leadexperience4,
                'leadskills5' : leadskills5,
                'leadexperience5' : leadexperience5,
                    # Add more key-value pairs as needed
                }
                print(data)

                # Sending a POST request with the data
                response = requests.post(url, data=data)

                # Check the response from the server


                print(response.text)  # Print the response from the API

                
                if response.status_code == 200:
                    id = emailleadid
                    print(id)
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                    messages.success(request, 'Your lead has been updated to Career.desss.com successfully!')  # Success message
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            
                elif response.status_code == 403:
                    id = emailleadid
                    print(id)
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                    # messages.success(request, 'Lead update was made. In our database, the job data you provided has already been updated!')  # Success message
                    messages.success(request, 'Your lead updated.In our database, the job data you provided has already been updated!')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                else:
                    messages.error(request, 'Your lead has not been updated to Career.desss.com!')  # Error message
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class whatsappbenchsales_view(View):
    
    def get(self,  request):
        
        details = Film.objects.filter(dropdownlist='Benchsales').order_by('id')

        page_number = request.GET.get('page', 1)
       
        # Create a Paginator object with your queryset and the number of items per page
        paginator = Paginator(details, 25)  # Change '10' to the number of items you want per page

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

        return render(request, 'whatsappbenchsales.html', context)
      

    def post(self, request, *args, **kwargs):
      
         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')
            # if product_ids == product_ids:
            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            print(product_ids)
            print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:
                    # product = Film.object.get(pk=id)
                    obj = get_object_or_404(Film, id = id)
                    obj.delete()
                return redirect('home')
            elif 'ids[]' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(snippet_ids)
                for id in snippet_ids:
             
                    print(id)
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                return redirect('whatsupbenchsales')
            elif 'id' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(delete_idd)
              
                id = delete_idd
                obj = get_object_or_404(Film, id=id)
                obj.delete()
                
                return redirect('whatsupbenchsales')
            else:
                return redirect('whatsupbenchsales')



def whatsappbenchsalesview(request,id):
    object=Film.objects.get(id=id)
    # details = Film.objects.filter(dropdownlist='Careersales').get(id=id)

   
    return render(request,'whatsappbenchsalesview.html',{'object':object,})

def whatsappbenchsalesedit(request, id):
    object_lead = Film.objects.get(id=id)
    content = object_lead.filmurl

    #  #Whatsapp api dropdowns
    # job_type = "https://career.desss.com/dynamic/careerdesssapi.php?action=job"
    # response = requests.get(job_type)
    # job_data = response.json()

    # # Extract "name" values from the API response
    # work_type_options = [item["name"] for item in job_data["data"]]

    # workplace = "https://career.desss.com/dynamic/careerdesssapi.php?action=workplace_type"
    # response = requests.get(workplace)
    # job_data = response.json()

    # # Extract "name" values from the API response
    # workplace_options = [item["name"] for item in job_data["data"]]
        
    # Email ID extraction
    email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
    email_match = email_pattern.search(content)
    email_id = email_match.group() if email_match else ''

    # Phone number extraction for multiple country formats
    # phone_pattern = re.compile(r'(?:\+1\s?)??[-.\s]?\d{3}[-.\s]?\d{4}|(?:\+44\s?)?)?\s?\d{4}[-.\s]?\d{6}|(?:\+91\s?)?\d{10}')
    # phone_match = phone_pattern.search(content)
    # phone_number = phone_match.group() if phone_match else ''
    phone_pattern = re.compile(r'(?:\+1\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|(?:\+44\s?)?\(?(?:0\))?\s?\d{4}[-.\s]?\d{6}|(?:\+91\s?)?\d{10}')
    phone_match = phone_pattern.search(content)
    phone_number = phone_match.group() if phone_match else ''

    # Address extraction
    address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?)\s+(\d{5})')
    address_match = address_pattern.search(content)
    street = address_match.group(1) if address_match else ''
    city = address_match.group(2) if address_match else ''
    state = address_match.group(3) if address_match else ''
    zip_code = address_match.group(4) if address_match else ''

    # Legal status extraction
    legalstatus_pattern = re.compile(r'(H1B|No H1B|Green Card|Citizen|Work Visa|Permanent Resident)', re.IGNORECASE)
    legalstatus_match = legalstatus_pattern.search(content)
    legal_status = legalstatus_match.group(1) if legalstatus_match else ''

    # Mobile number extraction
    mobile_pattern = re.compile(r'Mob:\s(\d+)')
    mobile_match = mobile_pattern.search(content)
    mobile_number = mobile_match.group(1) if mobile_match else ''


    # Location extraction
    location_pattern = re.compile(r'Location\s*:\s*(.*?)\s*Preferred\s*location', re.IGNORECASE)
    location_match = location_pattern.search(content)
    location = location_match.group(1).strip() if location_match else ''



    # Create a dictionary to store the extracted information
    extracted_data = {
        "email_id": email_id,
        "phone_number": phone_number,
        "Location:": location,
        "street": street,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "legal_status": legal_status,
        "mobile_number": mobile_number,
        "object_lead":object_lead,
        # "work_type_options": work_type_options,
        # "workplace_options": workplace_options,

    }

    # Now you can use the extracted_data dictionary as needed, such as storing it in a database or processing it further.
    # print(extracted_data)
   

    # return render(request, 'whatsappbenchsalesedit.html', {'object_lead':object_lead})
    return render(request, 'whatsappbenchsalesedit.html', extracted_data)

def whatsappbenchsalescreate(request):
    if request.method=="POST":
        
        if 'chiliadstaffingapi' in request.POST:
            benchfirstname=request.POST['benchfirstname']
            benchlastname=request.POST['benchlastname']
            benchexperience=request.POST['benchexperience']
            Rate=request.POST['Rate']
          
            Position=request.POST['Position']
            Location=request.POST['Location']
            Duration=request.POST['Duration']
            benchrelocation=request.POST['benchrelocation']
            Legal_Status=request.POST['Legal_Status']
            benchnoticeperiod=request.POST['benchnoticeperiod']
            benchsalesfirstname=request.POST['benchsalesfirstname']
            benchsaleslastname=request.POST['benchsaleslastname']
            benchsalescompany=request.POST['benchsalescompany']
            benchsalesemail=request.POST['benchsalesemail']
            benchsalesmobile=request.POST['benchsalesmobile']
            benchsalesaddress=request.POST['benchsalesaddress']
            Interview_Type=request.POST['Interview_Type']
            Work_Type=request.POST['Work_Type']
            Remote=request.POST['Remote']
            # obj=Film.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,benchcurrentlocation=benchcurrentlocation,benchtechnology=benchtechnology,benchrelocation=benchrelocation,benchvisa=benchvisa,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress)
            # obj.save()
            # print(leademail)
                            
           
            # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
            # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
            # response = requests.get(url)
            # print(response.text)  # Print the response from the API
    
            if response.status_code == 200:
                        
                            messages.success(request, 'Your lead has been updated to chiliadstaffing.com successfully!')  # Success message
                            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
 
            elif response.status_code == 403:
                        
                            # messages.success(request, 'No update was made. In our database, the data you provided has already been updated!')  # Success message
                            messages.success(request, 'Lead update was made. In our database, the job data you provided has already been updated!')
                            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                messages.error(request, 'Your lead has not been updated to chiliadstaffing.com!')  # Error message
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            return redirect('customemailleads')


                        
        elif 'careerdesssapi' in request.POST:
                benchfirstname=request.POST['benchfirstname']
                benchlastname=request.POST['benchlastname']
                benchexperience=request.POST['benchexperience']
                Rate=request.POST['Rate']
            
                Position=request.POST['Position']
                Location=request.POST['Location']
                Duration=request.POST['Duration']
                benchrelocation=request.POST['benchrelocation']
                Legal_Status=request.POST['Legal_Status']
                benchnoticeperiod=request.POST['benchnoticeperiod']
                benchsalesfirstname=request.POST['benchsalesfirstname']
                benchsaleslastname=request.POST['benchsaleslastname']
                benchsalescompany=request.POST['benchsalescompany']
                benchsalesemail=request.POST['benchsalesemail']
                benchsalesmobile=request.POST['benchsalesmobile']
                benchsalesaddress=request.POST['benchsalesaddress']
                Interview_Type=request.POST['Interview_Type']
                Work_Type=request.POST['Work_Type']
                Remote=request.POST['Remote']
                emailleadid = request.POST['emailleadid']
                #print(leademail)
                # obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadposition=leadposition,leaddescription=leaddescription,
                # leadlocation = leadlocation,leadduration = leadduration, leadlegalstatus = leadlegalstatus,leadinterviewtype = leadinterviewtype,leadworktype = leadworktype,leadremote = leadremote,
                # leadexperience = leadexperience,leadrate = leadrate,  leadskills1 = leadskills1,leadexperience1 = leadexperience1, leadskills2 = leadskills2,leadexperience2 = leadexperience2, leadskills3 = leadskills3, leadexperience3 = leadexperience3, leadskills4 = leadskills4, leadexperience4 = leadexperience4, leadskills5 =leadskills5,
                # leadexperience5 = leadexperience5,)
                # obj.save()
                # django inbuilt function for removing html tags
            
      
                # URL for the API endpoint
                url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&Rate={Rate}&Position={Position}&Location={Location}&Duration={Duration}&relocation={benchrelocation}&Legal_Status={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}"

                
                # Sending a POST request with the data
                response = requests.get(url)

                # Check the response from the server


                print(response.text)  # Print the response from the API

                
                if response.status_code == 200:
                    id = emailleadid
                    print(id)
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                    messages.success(request, 'Your lead has been updated to Career.desss.com successfully!')  # Success message
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            
                elif response.status_code == 403:
                    id = emailleadid
                    print(id)
                    status = Film.objects.get(id=id)
                    print(status)
                    status.checkstatus^= 1
                    status.save()
                    # messages.success(request, 'Lead update was made. In our database, the job data you provided has already been updated!')  # Success message
                    messages.success(request, 'Your lead updated. In our database, the job data you provided has already been updated!')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                else:
                    messages.error(request, 'Your lead has not been updated to Career.desss.com!')  # Error message
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))