from django.contrib import admin
from django.urls import path , include
from . import views

urlpatterns = [
    path("" , views.login_view , name="login"),
    path("" , views.logout_view , name="logout"),
    path("home" , views.home , name="home"),
    path("balance" , views.balance_view , name="balance"),
    path("split_equally" , views.split_equally , name="split_equally")
]
