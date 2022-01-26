from django.urls import path
from django.views.generic import TemplateView
from .views import Dashboard

app_name = 'home'

urlpatterns = [
    # path('', TemplateView.as_view(template_name='home/index.html'), name='index'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
]
