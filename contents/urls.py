from django.urls import path

from . import views
from contents.views import (CustomWebcontent_view, Customblog_view)


urlpatterns = [
    path("", views.index, name="index"),
    path('customwebcontentsfile/', views.customwebcontentsfile, name='customwebcontentsfile'),
    path('customwebcontentleads/',CustomWebcontent_view.as_view(),name="customwebcontentleads"),
    path('customwebcontentview/<int:id>',views.Customwebcontentview, name="customwebcontentview"),
    path('blogfile/', views.blogfile, name='blogfile'),
    path('blog/',Customblog_view.as_view(),name="blog"),
    path('blogview/<int:id>',views.blogview,name="blogview"),
]
