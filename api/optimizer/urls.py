from django.urls import path

from .views import SolveView

urlpatterns = [
    path("solve/", SolveView.as_view(), name="solve"),
]