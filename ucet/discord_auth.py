from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from .discord_client import DiscordClient

UserModel = get_user_model()

class DiscordAuth(ModelBackend):
    
    def authenticate(self, request, id, token):
        client = DiscordClient()
        
        if token is None or id is None:
            return
        
        try:
            user = UserModel._default_manager.get(discord_id=id)
            token = user.access_token
            discord_user = client.identify_user()
        except UserModel.DoesNotExist:
            return
        else:
            if self.user_can_authenticate(user):
                return user