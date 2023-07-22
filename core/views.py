from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse
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
from .forms import WhatsappForm, FilmForm, LocationChoiceField, LabelChoiceField, DateChoiceField, CustomleadsForm, UploadFileForm, EmailbenchsalesForm, EmailleadoppurtunitiesForm, EmailsampleForm, CustomizeEmailLeadsForm, CustomizeBenchsalesLeadsForm, CustomemailleadsForm, CustombenchsalesForm
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


# dot='./media/'
dot = '/var/www/subdomain/whatsappdata/analysis/media/'

def customemailleadsfile(request):
    # cache.clear()

    username = " username"
    password = "password"

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
                    break
        else:
            email_body = parsed_email.get_payload(decode=True).decode("utf-8", errors="ignore")

        # Write the email information to the CSV file
        csv_writer.writerow([subject, sender, received_time, email_body])

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
                # email data savings
                text = row[3]
                # Extracting first name and last name using regex
                name_pattern = re.compile(r'From:\s([^<]+)')
                match = name_pattern.search(text)

                phone_pattern = re.compile(r'Office:\s(\(\d{3}\)\s\d{3}-\d{4})')
                phone_match = phone_pattern.search(text)

                company_pattern = re.compile(r'From:\s[^<]+\s<([^@]+@[^>]+)>')
                company_match = company_pattern.search(text)

                address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?)\s+(\d{5})')
                address_match = address_pattern.search(text)

                # address_pattern = re.compile(r'\d+\s+(.*?),\s+(.*?),\s+(.*?),\s+(\d{5})')
                # address_match = address_pattern.search(text)

                legalstatus_pattern = re.compile(r'(H1B|Green Card|Citizen|Work Visa|Permanent Resident)', re.IGNORECASE)
                legalstatus_match = legalstatus_pattern.search(text)

                mobile_pattern = re.compile(r'Mob:\s(\d+)')
                mobile_match = mobile_pattern.search(text)



                if match:
                    name = match.group(1).strip()
                    first_name, _, last_name = name.partition(" ")
                    email_id = re.search(r'<([^>]+)>', text).group(1)
                    # Extracting description using regex
                    description_pattern = re.compile(r'Subject:.*?\n\n(.*)', re.DOTALL)
                    match = description_pattern.search(text)

                    if match:
                        description = match.group(1).strip()
                    else:
                        description = ""

                    if phone_match:
                        phone_number = phone_match.group(1).strip()
                    else:
                        phone_number = ""

                    if company_match:
                        company_email = company_match.group(1).strip()
                        company_name = company_email.split('@')[1].strip()
                    else:
                        company_name = ""

                    if address_match:
                        address = address_match.group(1).strip()
                        city = address_match.group(2).strip()
                        state = address_match.group(3).strip()
                        zipcode = address_match.group(4).strip()
                    else:
                        address = ""
                        city = ""
                        state = ""
                        zipcode = ""

                    if legalstatus_match:
                        legalstatus = legalstatus_match.group(0).strip()
                    else:
                        legalstatus = ""

                    if mobile_match:
                        mobile_number = mobile_match.group(1).strip()
                    else:
                        mobile_number = ""



                    # Extracting position, location, and duration using regex
                    position_pattern = re.compile(r'Position:\s(.*?)\n')
                    location_pattern = re.compile(r'Location:\s(.*?)\n')
                    duration_pattern = re.compile(r'Duration:\s(.*?)\n')

                    position_match = position_pattern.search(text)
                    location_match = location_pattern.search(text)
                    duration_match = duration_pattern.search(text)

                    position = position_match.group(1).strip() if position_match else ""
                    location = location_match.group(1).strip() if location_match else ""
                    duration = duration_match.group(1).strip() if duration_match else ""

                else:
                    first_name = ""
                    last_name = ""
                    email_id = ""
                    description = ""
                    position = ""
                    location = ""
                    duration = ""
                    phone_number = ""
                    company_name = ""

                # Output the extracted fields
                print("First Name:", first_name)
                print("Last Name:", last_name)
                print("Email ID:", email_id)
                print("Description:", description)
                print("Position:", position)
                print("Location:", location)
                print("Duration:", duration)
                print("Phone Number:", phone_number)
                print("Company:", company_name)
                print("Address:", address)
                print("City:", city)
                print("State:", state)
                print("Zipcode:", zipcode)
                print("Legalstatus:", legalstatus)
                print("Mobile Number:", mobile_number)
                customleadsdata, created = Customleads.objects.get_or_create(
                    leadfirstname = first_name,
                    leadlastname = last_name,
                    leademail = email_id,
                    leadusername = first_name+' '+last_name,
                    leadpassword  = 'Desss@123',
                    leadcompany = company_name,
                    leadphonenumber = phone_number,
                    leadaddress = address,
                    leadaddress2 = '',
                    leadcity = city,
                    leadstate = state,
                    leadzipcode = zipcode,
                    leadposition = position,
                    leaddescription = description,
                    leadlocation = location,
                    leadduration = duration,
                    leadlegalstatus = legalstatus,
                    leadinterviewtype = '',
                    leadworktype = '',
                    leadremote = '',
                    leadexperience = '',
                    leadrate = '',
                   )
                if created:
                    customleadsdata.save()
                    print('done')

                    print('done')
                            # if os.path.exists(filename):
                            #     os.remove(filename)
                            #     print('removed')         
                            
            else:
                print("That file does not exist!")
                return redirect('customemailleads') 

                        
                        # if os.path.exists(filename):
                        #     os.remove(filename)
                        #     print('removed')
    if os.path.exists(emailfileleads):
        os.remove(emailfileleads)
        print('removed')
            # return render(request, 'emailbenchsalesdupload.html', {})
        return redirect('customemailleads')    
    # return HttpResponse('ok')
    return redirect('customemailleads')    


def custombenchsalesfile(request):
    # cache.clear()

    username = " username"
    password = "password"

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
                    break
        else:
            email_body = parsed_email.get_payload(decode=True).decode("utf-8", errors="ignore")

        # Write the email information to the CSV file
        csv_writer.writerow([subject, sender, received_time, email_body])

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
            print(row)
            print('passed')
                        
            customleadsa, created = Custombenchsales.objects.get_or_create(
                bstodaysdate = todaydatevalue,
                bsSubject = row[0],
                bsFrom = row[1],
                bsReceived_Time = row[2],
                bsEmail_Body = row[3],
                )
            if created:
                customleadsa.save()
                print('done')
                            # if os.path.exists(filename):
                            #     os.remove(filename)
                            #     print('removed')         
                            
            else:
                print("That file does not exist!")
                return redirect('custombenchsales') 

                        
                        # if os.path.exists(filename):
                        #     os.remove(filename)
                        #     print('removed')
    if os.path.exists(emailfileleads):
        os.remove(emailfileleads)
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
    return HttpResponse('hello world')


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

def customemailleadsedits(request,id):
    object=Customleads.objects.get(id=id)

   
    return render(request,'customemailleadsedits.html',{'object':object,})

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
            # elif 'chiliadstaffingapi' in request.POST:
            #     id = my_model.id
            #     if id==id:
            #         firstname = my_model.leadfirstname
            #         lastname = my_model.leadlastname
            #         experience = my_model.leademail
            #         currentlocation = my_model.leadusername
            #         technology = my_model.leadpassword
            #         relocation = my_model.Relocation
            #         visa = my_model.Visa
            #         noticeperiod = my_model.Notice_Period
            #         benchsalesfirstname = my_model.Benchsales_First_Name
            #         benchsaleslastname = my_model.Benchsales_Last_Name
            #         benchsalescompany = my_model.Benchsales_Company
            #         benchsalesemail = my_model.Benchsales_Email
            #         benchsalesmobile = my_model.Benchsales_Mobile
            #         benchsalesaddress = my_model.Benchsales_Address
            #         unwanted = "[%]"
            #         originaldata = re.sub(unwanted, '', benchsalesaddress)
                    
            #         # title = my_model.title
            #         url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=benchsales_lead&firstname={firstname}&lastname={lastname}&experience={experience}&currentlocation={currentlocation}&technology={technology}&relocation={relocation}&visa={visa}&noticeperiod={noticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"
            #         # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
            #         response = requests.get(url)
            #         print(response.text)  # Print the response from the API
            #         status = Customleads.objects.get(id=id)
            #         print(status)
            #         status.bcheckstatus^= 1
            #         status.save()
            #         return redirect('customemailleads')
            #         # return redirect('search')
            #     return redirect('customemailleadadd', id)

                
            # elif 'careerdesssapi' in request.POST:
            #     id = my_model.id
            #     if id==id:
            #         firstname = my_model.First_Name
            #         lastname = my_model.Last_Name
            #         experience = my_model.Experience
            #         currentlocation = my_model.Current_Location
            #         technology = my_model.Technology
            #         relocation = my_model.Relocation
            #         visa = my_model.Visa
            #         noticeperiod = my_model.Notice_Period
            #         benchsalesfirstname = my_model.Benchsales_First_Name
            #         benchsaleslastname = my_model.Benchsales_Last_Name
            #         benchsalescompany = my_model.Benchsales_Company
            #         benchsalesemail = my_model.Benchsales_Email
            #         benchsalesmobile = my_model.Benchsales_Mobile
            #         benchsalesaddress = my_model.Benchsales_Address
            #         unwanted = "[%]"
            #         originaldata = re.sub(unwanted, '', benchsalesaddress)
                    
            #         # title = my_model.title
            #         url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={firstname}&lastname={lastname}&experience={experience}&currentlocation={currentlocation}&technology={technology}&relocation={relocation}&visa={visa}&noticeperiod={noticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"
            #         # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
            #         response = requests.get(url)
            #         print(response.text)  # Print the response from the API

            #         status = Customleads.objects.get(id=id)
            #         print(status)
            #         status.bcheckstatus^= 1
            #         status.save()
            #         return redirect('customemailleads')
            #         # return redirect('search')
            #     return redirect('customemailleadadd', id)
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
                    cleaned_leaddescription = leaddescription.replace("<br>", "")
                    obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadposition=leadposition,leaddescription=cleaned_leaddescription,
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
                        status = Custombenchsales.objects.get(id=id)
                        # status = get_object_or_404(Customleads, id=id)
                        print(status)
                        status.bscheckstatus^= 1
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
                        cleaned_leaddescription = leaddescription.replace("<br>", "")
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
#    return redirect('customemailleads') 

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



class CustomEmailleads_view(View):
    

    def get(self,  request):
        # location_list = LocationChoiceField()
        # label_list = LabelChoiceField()
        # datesdatalist = DateChoiceField()


        if 'q' in request.GET:
            q = request.GET['q']
            # data = Film.objects.filter(filmurl__icontains=q)
            multiple_q = Q(Q(todaysdate__icontains=q) | Q(Subject__icontains=q) | Q(From_icontains=q) | Q(Received_Time_icontains=q) | Q(Email_Body_icontains=q))
            details = Customemailleads.objects.filter(multiple_q)
            # object=Film.objects.get(id=id)
        elif request.GET.get('locations'):
            selected_location = request.GET.get('locations')
            details = Customemailleads.objects.filter(bcheckstatus=selected_location)
        elif request.GET.get('label'):
            labels = request.GET.get('label')
            details = Customemailleads.objects.filter(bdropdownlist=labels)#.filter(dropdownlist='New')
        elif request.GET.get('datesdata'):
            selected_datedata = request.GET.get('datesdata')
            details = Customemailleads.objects.filter(bdropdownlist='Benchsales',title=selected_datedata)
        else:

            details = Customemailleads.objects.order_by('id')
        context = {
            'details': details,

            # 'label_list': label_list,

           
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

                    obj = get_object_or_404(Customemailleads, id = id)
                    obj.delete()
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
    # if request.method=="POST":
    if 'save_home' in request.POST:
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
        return redirect('customemailleads')
        
    elif 'chiliadstaffingapi' in request.POST:
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
        # unwanted = "[%]"
        # originaldata = re.sub(unwanted, '', leaddescription)
                        
        # title = my_model.title
        # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}"
        url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
        # url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
        response = requests.get(url)
        print(response.text)  # Print the response from the API
                        # status = Emailbenchsales.objects.get(id=id)
                        # print(status)
                        # status.bcheckstatus^= 1
                        # status.save()
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
            #   leadoccupation=request.POST['leadoccupation']
            #   leaddescription=request.POST['leaddescription']

            #   obj=Customleads.objects.create(leadfirstname=leadfirstname,leadlastname=leadlastname,leademail=leademail,leadusername=leadusername,leadpassword=leadpassword,leadcompany=leadcompany,leadphonenumber=leadphonenumber,leadaddress=leadaddress,leadaddress2=leadaddress2,leadcity=leadcity,leadstate=leadstate,leadzipcode=leadzipcode,leadoccupation=leadoccupation,leaddescription=leaddescription)
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
                # originaldata = re.sub(unwanted, '', benchsalesaddress)
                            
                            # title = my_model.title
            # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}"
            url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=employer_lead&firstname={leadfirstname}&lastname={leadlastname}&email={leademail}&username={leadusername}&password={leadpassword}&company={leadcompany}&phonenumber={leadphonenumber}&address={leadaddress}&address2={leadaddress2}&city={leadcity}&state={leadstate}&zipcode={leadzipcode}&occupation={leadposition}&description={leaddescription}&leadlocation={leadlocation}&leadduration={leadduration}&leadlegalstatus={leadlegalstatus}&leadinterviewtype={leadinterviewtype}&leadworktype={leadworktype}&leadremote={leadremote}&leadexperience={leadexperience}&leadrate={leadrate}"
     
                            # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=newlead&firstname={firstname}&lastname={lastname}&email={email}&username={username}&password={password}&company={company}&phonenumber={phonenumber}&address={address}&address2={address2}&city={city}&state={state}&zipcode={zipcode}&occupation={occupation}&description={description}"
            response = requests.get(url)
            print(response.text)  # Print the response from the API

                # status = Emailbenchsales.objects.get(id=id)
                # print(status)
                # status.bcheckstatus^= 1
                # status.save()
            return redirect('customemailleads')
                            # return redirect('search')
            #   return redirect('emailbenchsalesedit', id)
    # else:
    #     form = EmailbenchsalesForm(instance=my_model)
    #     return redirect(request.META['HTTP_REFERER'])
    # return redirect('customemailleads')



class CustomBenchsales_view(View):
    

    def get(self,  request):
        # location_list = LocationChoiceField()
        # label_list = LabelChoiceField()
        # datesdatalist = DateChoiceField()


        if 'q' in request.GET:
            q = request.GET['q']
            # data = Film.objects.filter(filmurl__icontains=q)
            multiple_q = Q(Q(bstodaysdate__icontains=q) | Q(bsSubject__icontains=q) | Q(bsFrom_icontains=q) | Q(bsReceived_Time_icontains=q) | Q(bsEmail_Body_icontains=q))
            details = Custombenchsales.objects.filter(multiple_q)
            # object=Film.objects.get(id=id)
        elif request.GET.get('locations'):
            selected_location = request.GET.get('locations')
            details = Custombenchsales.objects.filter(bcheckstatus=selected_location)
        elif request.GET.get('label'):
            labels = request.GET.get('label')
            details = Custombenchsales.objects.filter(bdropdownlist=labels)#.filter(dropdownlist='New')
        elif request.GET.get('datesdata'):
            selected_datedata = request.GET.get('datesdata')
            details = Custombenchsales.objects.filter(bdropdownlist='Benchsales',title=selected_datedata)
        else:

            details = Custombenchsales.objects.order_by('id')
        context = {
            'details': details,

            # 'label_list': label_list,

           
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

                    obj = get_object_or_404(Custombenchsales, id = id)
                    obj.delete()
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


def Custombenchsalescreate(request):
    # if request.method=="POST":
    if 'save_home' in request.POST:
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

        obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress,Interview_Type=Interview_Type,Work_Type=Work_Type,Remote=Remote)
        obj.save()

        return redirect('custombenchsales')
        
    elif 'chiliadstaffingapi' in request.POST:
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

        obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress,Interview_Type=Interview_Type,Work_Type=Work_Type,Remote=Remote)
        obj.save()
 
                        
        # title = my_model.title
        url = f"https://chiliadstaffing.com/dynamic/chiliadstaffingapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&Rate={Rate}&Position={Position}&Location={Location}&Duration={Duration}&relocation={benchrelocation}&Legal_Status={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}"

        response = requests.get(url)
        print(response.text)  # Print the response from the API

        return redirect('custombenchsales')

                    
    elif 'careerdesssapi' in request.POST:
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

        obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,Rate=Rate,Position=Position,Location=Location,Duration=Duration,benchrelocation=benchrelocation,Legal_Status=Legal_Status,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress,Interview_Type=Interview_Type,Work_Type=Work_Type,Remote=Remote)
        obj.save()
                            
                            # title = my_model.title
        # url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&currentlocation={Location}&technology={Position}&relocation={benchrelocation}&visa={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"

        url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&Rate={Rate}&Position={Position}&Location={Location}&Duration={Duration}&relocation={benchrelocation}&Legal_Status={Legal_Status}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}&Interview_Type={Interview_Type}&Work_Type={Work_Type}&Remote={Remote}"
     
     
        response = requests.get(url)
        print(response.text)  # Print the response from the API

        return redirect('custombenchsales')

                    
    elif 'careerdesssapi' in request.POST:
        benchfirstname=request.POST['benchfirstname']
        benchlastname=request.POST['benchlastname']
        benchexperience=request.POST['benchexperience']
        benchcurrentlocation=request.POST['benchcurrentlocation']
        benchtechnology=request.POST['benchtechnology']
        benchrelocation=request.POST['benchrelocation']
        benchvisa=request.POST['benchvisa']
        benchnoticeperiod=request.POST['benchnoticeperiod']
        benchsalesfirstname=request.POST['benchsalesfirstname']
        benchsaleslastname=request.POST['benchsaleslastname']
        benchsalescompany=request.POST['benchsalescompany']
        benchsalesemail=request.POST['benchsalesemail']
        benchsalesmobile=request.POST['benchsalesmobile']
        benchsalesaddress=request.POST['benchsalesaddress']

        obj=Custombench.objects.create(benchfirstname=benchfirstname,benchlastname=benchlastname,benchexperience=benchexperience,benchcurrentlocation=benchcurrentlocation,benchtechnology=benchtechnology,benchrelocation=benchrelocation,benchvisa=benchvisa,benchnoticeperiod=benchnoticeperiod,benchsalesfirstname=benchsalesfirstname,benchsaleslastname=benchsaleslastname,benchsalescompany=benchsalescompany,benchsalesemail=benchsalesemail,benchsalesmobile=benchsalesmobile,benchsalesaddress=benchsalesaddress)
        obj.save()
                            
                            # title = my_model.title
        url = f"https://career.desss.com/dynamic/careerdesssapi.php?action=benchsales_lead&firstname={benchfirstname}&lastname={benchlastname}&experience={benchexperience}&currentlocation={benchcurrentlocation}&technology={benchtechnology}&relocation={benchrelocation}&visa={benchvisa}&noticeperiod={benchnoticeperiod}&benchsalesfirstname={benchsalesfirstname}&benchsaleslastname={benchsaleslastname}&benchsalescompany={benchsalescompany}&benchsalesemail={benchsalesemail}&benchsalesmobile={benchsalesmobile}&benchsalesaddress={benchsalesaddress}"
     
     
        response = requests.get(url)
        print(response.text)  # Print the response from the API

        return redirect('custombenchsales')