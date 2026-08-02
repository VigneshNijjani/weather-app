"""
URL configuration for wheater project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app1 import views


urlpatterns = [
    path("", views.welcome, name="welcome"),

    path('admin/', admin.site.urls),

    path("city/", views.city, name="city"),

    path("fetch_city/", views.fetch_city, name="fetch_city"),

    path("weather/", views.city_weather, name="city_weather"),

    path("login/",views.login,name="login"),

    path("register/",views.register,name="register")

]