from django.urls import path, re_path
from . import views

app_name='matches'

urlpatterns = [
    path("", views.MatchesList.as_view(), name='match-list'),   
    path("create/", views.MatchesCreate.as_view(), name='match-create'),
    path("<int:pk>/update/", views.MatchesUpdate.as_view(), name='match-update'),
    path("<int:pk>/", views.MatchesDetail.as_view(), name='match-detail'),
    
    
    # JSON API
    path("<int:pk>/detail/", views.MatchDetailJSON.as_view(), name='match-detail-json'),
    path("<int:pk>/<str:option>/", views.MatchParticipantCD.as_view(), name='match-participant-cd'),
    # Round
    path("<int:pk>/kolo/add/", views.AddRound.as_view(), name='match-round-add'),
    path("<int:pk>/kolo/<int:round_order>/", views.RoundResultsJSON.as_view(), name='match-round-results'),
    
]
