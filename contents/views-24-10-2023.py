from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
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
# Create your views here.
# import required librarys
import os
import re
import csv
import smtplib
import imaplib
import email
from django.db.models import Q
from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from django.views.generic import View
from bs4 import BeautifulSoup


from .models import Customwebcontent, blogbenchsales
from .forms import CustomwebcontentForm, blogbenchsalesForm


def index(request):
    return HttpResponse('Hello World')

#cache removal 

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

# Web content 

# dot='./media/contents/'
dot = '/var/www/subdomain/whatsappdata/analysis/media/contents/'
from dateutil import parser
def customwebcontentsfile(request):
    cache.clear()

    # username = "careersales@desss.com"
    # password = "!!!H0u$on@77042$$$"
    username = "zzzwebcontent@desss.com"
    password = "!@#!nnanagar@600101$%^"

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

    emailfileleads = dot + str("email_web_Content_datas.csv")
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
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    email_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif content_type == "text/html":
                    email_html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
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
        if  email_body == "":
            cleantext = BeautifulSoup(email_html, "lxml").text
            email_body = cleantext
        csv_writer.writerow([subject, sender, received_time, email_body, email_html])
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
            print(row)
            print('passed')
                        
            customweb, created = Customwebcontent.objects.get_or_create(
                webtodaysdate = todaydatevalue,
                webSubject = row[0],
                webFrom = row[1],
                webReceived_Time = row[2],
                webEmail_Body = row[3],
                webEmail_Bodyhtml = row[4],
                )
            if created:
                customweb.save()
                print('started')
                # email data savings
                            
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
        return redirect('customwebcontentleads')    
    # return HttpResponse('ok')
    return redirect('customwebcontentleads')    



def convert_to_datetime(date_string):
    return dt.strptime(date_string, '%d-%m-%Y').date()

class CustomWebcontent_view(View):
    

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
        
        details = Customwebcontent.objects.filter(webcheckstatus=1).order_by('-id')

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
        return render(request, 'contents/customwebcontentlead.html', context)

    def post(self, request, *args, **kwargs):

         if request.method=="POST":
            product_ids=request.POST.getlist('id[]')

            snippet_ids=request.POST.getlist('ids[]')
            delete_idd=request.POST.get('id')
            # print(product_ids)
            # print(snippet_ids)
            if 'id[]' in request.POST:
                print(product_ids)
                for id in product_ids:

                    # obj = get_object_or_404(Customemailleads, id = id)
                    # obj.delete()
                    status = Customwebcontent.objects.get(id=id)
                    # print(status)
                    status.webcheckstatus^= 1
                    status.save()
                return redirect('customemailleads')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = Customwebcontent.objects.get(id=id)
                    print(status)
                    status.webcheckstatus^= 1
                    status.save()
                return redirect('customemailleads')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(Customwebcontent, id=id)
                obj.delete()
                
                return redirect('customemailleads')
            else:
                return redirect('customemailleads')


def Customwebcontentview(request,id):
    object=Customwebcontent.objects.get(id=id)

   
    return render(request,'contents/customwebcontentleadview.html',{'object':object,})


def blogfile(request):
    # cache.clear()

    username = "zzzblogyyy@desss.com"
    password = "!@#!nnanagar@600101$%^"

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
                        
            customleadsa, created = blogbenchsales.objects.get_or_create(
                blogtodaysdate = todaydatevalue,
                blogSubject = row[0],
                blogFrom = row[1],
                blogReceived_Time = row[2],
                blogEmail_Body = row[3],
                blogEmail_Bodyhtml = row[4],
                )
            if created:
                customleadsa.save()
                print('done')
                  
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
        return redirect('blog')    
    # return HttpResponse('ok')
    return redirect('blog')


class Customblog_view(View):
    

    def get(self,  request):
   
        details = blogbenchsales.objects.filter(blogcheckstatus=1).order_by('-id')
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
        return render(request, 'contents/blog.html', context)

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
                    status = blogbenchsales.objects.get(id=id)
                    # print(status)
                    status.blogcheckstatus^= 1
                    status.save()
                return redirect('blog')
            elif 'ids[]' in request.POST:

                print(snippet_ids)
                for id in snippet_ids:
   
                    print(id)
                    status = blogbenchsales.objects.get(id=id)
                    print(status)
                    status.blogcheckstatus^= 1
                    status.save()
                return redirect('blog')
            elif 'id' in request.POST:

                print(delete_idd)
     
                id = delete_idd
                obj = get_object_or_404(blogbenchsales, id=id)
                obj.delete()
                
                return redirect('blog')
            else:
                return redirect('blog')
            
def blogview(request,id):
    object=blogbenchsales.objects.get(id=id)

   
    return render(request,'contents/blogview.html',{'object':object,})