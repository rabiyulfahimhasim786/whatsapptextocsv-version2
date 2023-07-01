from django.urls import path

from . import views
from .views import (EmailLeads_view)
urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload'),
    path('emailscraper/', views.emailscraper, name='emailscraper'),
    # path('retrieve/', views.retrieve, name="retrieve"),
    path('email/', EmailLeads_view.as_view(), name="email"),
    path('emailedit/<int:id>',views.edit,name="emailedit"),
    path('emailupdate/<int:id>',views.update,name="emailupdate"),
    path('emaildelete/<int:id>',views.delete,name="emaildelete"),
]