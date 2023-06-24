from django.urls import path 
from  . import views 
from core.views import (Product_view, SnippetList, Leads_view, Emailproduct_view, Emailopp_view)

from django.urls import re_path
urlpatterns = [
    path('index/',views.index, name='index'),
    path('getDatapoint/',views.getDatapoint, name='getDatapoint'),
    path('upload/', views.upload_txt, name='upload_txt'),
    # path('', views.upload_txt, name='upload_txt'),
    # path('retrieve/',views.retrieve,name="retrieve"),
    path('edit/<int:id>',views.edit,name="edit"),
    path('leadedit/<int:id>',views.leadedit,name="leadedit"),
    path('emailleadedit/<int:id>',views.emailleadedit,name="emailleadedit"),
    path('emailleadoppurtunitiesedit/<int:id>',views.emailleadoppedit,name="emailleadoppurtunitiesedit"),
    path('update/<int:id>',views.update,name="update"),
    path('emailleadupdate/<int:id>',views.emailleadupdate,name="emailleadupdate"),
    path('emailleadoppupdate/<int:id>',views.emailleadoppupdate,name="emailleadoppupdate"),
    path('leadupdate/<int:id>',views.leadupdate,name="leadupdate"),
    # path('leadupdate/<int:id>',views.emailleadoppupdate,name="leadupdate"),
    path('delete/<int:id>',views.delete,name="delete"),
    path('opportunities/',views.search, name="search"),
    path('', Product_view.as_view(), name="home"),
    path('emailhome/', Emailproduct_view.as_view(), name="emailhome"),
    path('emailleadoppurtunities/', Emailopp_view.as_view(), name="emailleadoppurtunities"),
    path('retrieve/', Product_view.as_view(), name="retrieve"),
    path('leads/', Leads_view.as_view(), name="leads"),
    path('status/<int:id>/', views.status, name='status'),
    re_path(r'snippets/$', SnippetList.as_view(), name='snippet-list'),
    path('snippets/', SnippetList.as_view(), name="snippet"),
    # path('locations/', views.locations, name="locations"),
]