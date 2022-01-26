from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
class Dashboard(LoginRequiredMixin, View):
    
    def get(self, request):
        return render(request, template_name='home/dashboard.html')