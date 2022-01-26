from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member, Profile


@receiver(post_save, sender = Member)
def create_user_profile(sender, instance, created, **kwargs):
    if not created: return
    Profile.objects.create(user=instance)



