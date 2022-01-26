from django.db import models
from django.contrib.auth.models import AbstractUser
from matches.models import Player, Game
import datetime
from itertools import chain

# Create your models here.
class Member(AbstractUser):
    discord_id = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100)
    refresh_token = models.CharField(max_length=100)
    avatar = models.CharField(max_length=100, null=True)
    joined_at = models.DateTimeField()
    roles = models.TextField()
    
    def __str__(self):
        return self.username
    
    def serialize(self):
        return {
            'avatar_url': self.avatar_url,
            'username': self.username,
        }
    
    @property
    def avatar_url(self):
        if not self.avatar:
            return 'https://i.ibb.co/7pw2wXF/CATS-weblogo.png'
        return 'https://cdn.discordapp.com/avatars/%s/%s.webp?size=256' \
                % (self.discord_id, self.avatar)
    
    def all_matches(self):
        matches = []
        for player in self.players.all():
            matches.append(player.participates_in.all())
        # flatten list to one dimension
        return list(chain(*matches))
       
    def save(self, *args, **kwargs):
        created = False
        if not self.pk:
            created = True
        super().save(*args, **kwargs)
        if created:
            profile = Profile(user=self)
            profile.save()
            player = Player(user=self, game=Game.objects.get(name='Battlefield 4'))
            player.save()
    

class Profile(models.Model):
    user = models.OneToOneField(Member, on_delete=models.CASCADE)
    country = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    birthday = models.DateField(null=True)
    
    def __str__(self):
        return self.user.username + "\'s profile"
    
    def get_age(self):
        if not self.birthday: return None
        today = datetime.date.today()
        return today.year - self.birthday.year \
                - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
    
    def days_to_birthday(self):
        if not self.birthday: return None
        today = datetime.date.today()
        if ((today.month, today.day) <= (self.birthday.month, self.birthday.day)):
            delta = datetime.date(today.year, self.birthday.month, self.birthday.day) \
                    - today
        else:
            delta = datetime.date(today.year + 1, self.birthday.month, self.birthday.day) \
                    - today
        
        return delta.days