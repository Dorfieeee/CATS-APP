from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from .discord_client import DiscordClient
from django.contrib.auth import login, logout
from myapp.settings import LOGOUT_REDIRECT_URL

# Create your views here.
class DiscordAuth(View):
    client = DiscordClient()
    

class Login(DiscordAuth):
    '''Handles Discord OAuth2 logic'''
    def get(self, request):
        if not request.user.is_authenticated:
            return render(request, 'ucet/login.html')
        else:
            return HttpResponseRedirect(reverse('home:dashboard'))

    def post(self, request):
        auth_url = self.client.build_auth_url(request)
        return HttpResponseRedirect(auth_url)

class LoginComplete(DiscordAuth):
    def get(self, request):
        
        user = self.client.authenticate(request)
        
        if not user:
            return HttpResponseRedirect(reverse('ucet:failure'))
        else:
            # log user in
            login(request, user)
            
        
        return HttpResponseRedirect(reverse('home:dashboard'))


class LoginFailure(View):
    template_name="ucet/login_failure.html"

    def get(self, request):
        return render(request, self.template_name)

class Logout(View):
    
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(LOGOUT_REDIRECT_URL)