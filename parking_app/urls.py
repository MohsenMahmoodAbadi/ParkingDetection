from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('mobile/', views.mobile_stream, name='mobile_stream'),
    path('test/', views.test_page, name='test'),
]