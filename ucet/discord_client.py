from urllib.error import HTTPError
import requests
import urllib.parse
from .models import Member
import myapp.settings as settings
import datetime


class DiscordClient():
    client_id = ''
    client_secret = ''
    guild_id = ''
    base_url = 'https://discord.com/api'
    auth_url = '%s/oauth2/authorize' % base_url
    access_token_url = '%s/oauth2/token' % base_url
    refresh_token_url = '%s/oauth2/token' % base_url
    redirect_url = '%s/ucet/login/complete' % settings.HOST_URL
    scope = ['identify', 'guilds.members.read']
    response_type = 'code'
    state = ''
    allowed_roles = ['474947339707088896', '474947886539603978']
    token_type = 'Bearer'
    
    def __init__(self) -> None:
        self.client_id = settings.DISCORD_APP_ID
        self.client_secret = settings.DISCORD_APP_SECRET
        self.guild_id = settings.CATS_ID
        
    
    def build_auth_url(self, request):
        self.state = request.POST.get('csrfmiddlewaretoken')
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_url,
            'response_type': self.response_type,
            'scope': ' '.join(self.scope),
            'state': self.state,
        }
        query = urllib.parse.urlencode(query=params, safe='')
        return '%s?%s' % (self.auth_url, query)
   
        
    def get_member(self, token):
        '''
        Accepts Access Token and returns Guild Member Object
        Member contains user data and his data linked to the guild
        '''        
        headers = {
            'Authorization': '%s %s' % (self.token_type, token)
        }
        
        url = '%s/users/@me/guilds/%s/member' % (self.base_url, self.guild_id)
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        
        return r.json()
    
    
    def authenticate(self, request):
        code = request.GET.get('code')
        state = request.GET.get('state')
        
        if state != self.state:
            return
        
        # Access Token Response
        acr = None
        try:
            acr = self.exchange_code(code)
            if not acr: return
        except HTTPError:
            return
        
        self.token_type = acr['token_type']
        
        member = self.get_member(acr['access_token'])
        # whether the user has not yet passed
        # the guild's Membership Screening requirements
        allowed_to_join = [r for r in member['roles'] if r in self.allowed_roles]
        if member['pending'] or not allowed_to_join:
            return None
        
        # Identified successfully, get user or create new one
        # and return it
        _user = member['user']
        try:
            # If user already exists, refresh token
            user = Member.objects.get(discord_id=_user['id'])
            
            user.access_token = acr['access_token']
            user.refresh_token = acr['refresh_token']
            user.save()
            
        except Member.DoesNotExist:
            # First time login
            joined_at = datetime.datetime.fromisoformat(member['joined_at'])
            
            if hasattr(member, 'nick'):
                username = member['nick']
            else:
                username = _user['username']
                
            user = Member(discord_id = _user['id'],
                        username = username,
                        avatar = _user['avatar'],
                        joined_at = joined_at,
                        roles = ','.join(member['roles']),
                        access_token = acr['access_token'],
                        refresh_token = acr['refresh_token'])
            user.save()
            
        return user      
    
    
    def exchange_code(self, code):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_url
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        r = requests.post(self.access_token_url, data=data, headers=headers)
        r.raise_for_status()
        return r.json()
    
    
    def refresh_token(self, refresh_token):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        r = requests.post(self.refresh_token_url, data=data, headers=headers)
        r.raise_for_status()
        return r.json()