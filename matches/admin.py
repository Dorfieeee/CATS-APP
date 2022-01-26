from django.contrib import admin

from . import models


# Register your models here.
admin.site.register(models.Game)
admin.site.register(models.Player)
admin.site.register(models.PlayerSession)
admin.site.register(models.Team)
admin.site.register(models.RoundSession)
admin.site.register(models.Role)
admin.site.register(models.Participant)
admin.site.register(models.Map)
admin.site.register(models.Match)
admin.site.register(models.TeamDraft)
admin.site.register(models.MatchLeader)
admin.site.register(models.MatchMap)
