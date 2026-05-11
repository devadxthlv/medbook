"""
Core URL patterns — home page and any site-wide pages.
"""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
]
