from django.shortcuts import render, redirect
from django.http import HttpResponse
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
from .models import whatsapp, Film, Emaillead, Emailleadoppurtunities
from .forms import WhatsappForm, FilmForm, LocationChoiceField, LabelChoiceField, DateChoiceField, UploadFileForm, EmailleadForm, EmailleadoppurtunitiesForm 
from rest_framework.response import Response
from django.contrib import messages
import os
import re
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
    return HttpResponse('hello world')


import re
import pandas as pd
import csv

import os

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
            
            elif option == 'email benchsales':

                try:
                    filename = dot + str(baseurls)
                    # Define the column names
                    fieldnames = ['Reference date', 'Reference time', 'Reference Mobile Number', 'Reference Details', 'User date', 'User time', 'User Mobile Number', 'User Details',]

                    # Read the text file
                    # with open('input.txt', 'r') as file:
                    with open(filename, 'r',  encoding="utf-8") as file:
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
                    with open(dot + 'media/modified_data.csv', 'w', newline='', encoding="utf-8") as file:
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
                    df = pd.read_csv(dot + 'media/modified_data.csv', encoding='utf8')
                    # df = df[df['message'].notna()]
                    
                    for _, row in df.iterrows():
                        # datetime_str = row[0]
                        # date_str = datetime_str.split()[0]
                        # time_str = datetime_str.split()[1]
                        
                        emaillead, created = Emaillead.objects.get_or_create(
                            userdate = row[0],
                            usertime = row[1],
                            usermob = row[2],
                            userdetails = row[3],
                            emailuserdate = row[4],
                            emailusertime = row[5],
                            emailusermob = row[6],
                            emailuserdetails = row[7]
                            # date=date_str,
                            # title=time_str,
                            # year=row[1],
                            # filmurl=row[2]
                        )
                        print('done')
                        if created:
                            emaillead.save()
                    
                    if os.path.exists(filename):
                        os.remove(filename)
                    else:
                        print("That file does not exist!")
                    
                    return render(request, 'form_upload.html', {})
                except Exception as e:
                    print(e)
                    error_message = "Please upload a valid file"
                    return render(request, 'form_upload.html', {'errortext':error_message})
            elif option == 'email opportunities':

                try:
                    filename = dot + str(baseurls)
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
                    df = pd.read_csv(dot + 'media/emailmodified_data.csv', encoding='utf8')
                    # df = df[df['message'].notna()]
                    
                    for _, row in df.iterrows():
                        # datetime_str = row[0]
                        # date_str = datetime_str.split()[0]
                        # time_str = datetime_str.split()[1]
                        
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

def emailleadedit(request,id):
    object=Emaillead.objects.get(id=id)

   
    return render(request,'emailleadedit.html',{'object':object,})

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
                    # return redirect('leads')
                    return redirect('search')
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
                    # return redirect('leads')
                    return redirect('search')
                return redirect('leadedit', id)
    else:
        form = FilmForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])

def emailleadupdate(request,id):
    my_model = get_object_or_404(Emaillead, id=id)
    if request.method == 'POST':
        form = EmailleadForm(request.POST, instance=my_model)
        if form.is_valid():
            form.save()
            # delete_idd=request.POST.get('id')
            if 'save_home' in request.POST:
                return redirect('emailhome')
            elif 'save_next' in request.POST:
                try:
                    next_model = Emaillead.objects.filter(id__gt=id).exclude(emaildropdownlist='New').order_by('id')[0]
                    return redirect('emailleadedit', id=next_model.id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'save_continue' in request.POST:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif 'save_convert' in request.POST:
                status = Emaillead.objects.get(id=id)
                print(status)
                status.emailcheckstatus^= 1
                status.save()
                try:
                    next_model = Emaillead.objects.filter(id__gt=id).exclude(emaildropdownlist='New').filter(emailcheckstatus=1).order_by('id')[0]
                    return redirect('emailleadedit', id=next_model.id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_d' in request.POST:
                # snippet_ids=request.POST.getlist('ids[]')
                print(id)
                try:
                    next_model = Emaillead.objects.filter(id__gt=id).exclude(emaildropdownlist='New').filter(emailcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Emaillead, id=id)
                    id=next_model.id
                    # obj = get_object_or_404(Film, id=id)
                    obj.delete()
                    return redirect('emailleadedit', id)
                except IndexError:
                    return render(request, 'navigation.html')
            elif 'delete_dynamic' in request.POST:
                try:
                    # next_model = Emaillead.objects.filter(id__gt=id).exclude(emaildropdownlist='New').filter(emailcheckstatus=1).order_by('id')[0]
                    next_model = Emaillead.objects.filter(id__gt=id).filter(emailcheckstatus=1).order_by('id')[0]
                    obj = get_object_or_404(Emaillead, id=id)
                    id = next_model.id
                    obj.delete()
                    return redirect('emailleadedit', id)
                except IndexError:
                    obj = get_object_or_404(Emaillead, id=id)
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
                    status = Emaillead.objects.get(id=id)
                    print(status)
                    status.emailcheckstatus^= 1
                    status.save()
                    # return redirect('leads')
                    return redirect('search')
                return redirect('emailleadedit', id)
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
                    status = Emaillead.objects.get(id=id)
                    print(status)
                    status.emailcheckstatus^= 1
                    status.save()
                    # return redirect('leads')
                    return redirect('search')
                return redirect('emailleadedit', id)
    else:
        form = EmailleadForm(instance=my_model)
    return redirect(request.META['HTTP_REFERER'])

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

class Emailproduct_view(View):
    

    def get(self,  request):
        # location_list = LocationChoiceField()
        label_list = LabelChoiceField()
        # datesdatalist = DateChoiceField()


        if 'q' in request.GET:
            q = request.GET['q']
            # data = Film.objects.filter(filmurl__icontains=q)
            multiple_q = Q(Q(usermob__icontains=q) | Q(userdetails__icontains=q))
            details = Emaillead.objects.filter(multiple_q).filter(Q(emaildropdownlist='New'))
            # object=Film.objects.get(id=id)
        elif request.GET.get('locations'):
            selected_location = request.GET.get('locations')
            details = Emaillead.objects.filter(emailcheckstatus=selected_location)
        elif request.GET.get('label'):
            labels = request.GET.get('label')
            details = Emaillead.objects.filter(emaildropdownlist=labels)#.filter(dropdownlist='New')
        elif request.GET.get('datesdata'):
            selected_datedata = request.GET.get('datesdata')
            details = Emaillead.objects.filter(emaildropdownlist='New',title=selected_datedata)
        else:

            details = Emaillead.objects.filter(emaildropdownlist='New').order_by('id')
        context = {
            'details': details,

            'label_list': label_list,

           
        }
        return render(request, 'emailretrieve.html', context)

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

                    obj = get_object_or_404(Emaillead, id = id)
                    obj.delete()
                return redirect('emailhome')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = Emaillead.objects.get(id=id)
                    print(status)
                    status.emailcheckstatus^= 1
                    status.save()
                return redirect('emailhome')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(Emaillead, id=id)
                obj.delete()
                
                return redirect('emailhome')
            else:
                return redirect('emailhome')             

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
