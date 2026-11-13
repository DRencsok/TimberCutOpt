from django.urls import path

from .views import HealthView, SolveView

urlpatterns = [
    path("solve/", SolveView.as_view(), name="solve"),
    path("health/", HealthView.as_view(), name="health"),
]
