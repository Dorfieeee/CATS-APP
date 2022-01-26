import json
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse

from .forms import MatchCreateForm
from .models import Map, Match, Player, PlayerSession, Role, RoundSession, Team
# Create your views here.

class MatchesList(LoginRequiredMixin, ListView):
    model = Match
    
class MatchesDetail(LoginRequiredMixin, DetailView):
    model = Match
    
    def get(self, request, *args, **kwargs):
        
        self.extra_context = {'results': self.model.results}
        
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
class MatchesCreate(LoginRequiredMixin, View):
    model = Match
    template = "matches/match_form.html"    
    fields = ['title', 'start_at', 'description', 'completed', 'maps', 'leaders', 'game', 'participants']

    def get(self, request):
        form = MatchCreateForm()
        ctx = {'form': form}
        return render(request, self.template, ctx)
    
    def post(self, request):
        form = MatchCreateForm(request.POST)
        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template, ctx)
        
        form.save()
        
        return redirect(reverse_lazy('matches:match-list'))
   
class MatchParticipantCD(LoginRequiredMixin, View):
    model = Match
    
    def post(self, request, pk, option):
        response = {}
        
        try:
            match = self.model.objects.filter(completed=False).get(pk=pk)
            if option == 'join':
                message = '%s uspesne prihlasen do' % request.user
                match.add_player(request.user)
            elif option == 'leave':
                message = '%s uspesne odhlasen z' % request.user
                match.remove_player(request.user)
            else: 
                raise Exception('%s is not supported' % option)
        except Exception as e:
            response['success'] = 'false'
            response['message'] = str(e)            
            return JsonResponse(response, status=404)
        
        response['success'] = 'true'
        response['message'] = '%s %s' % (message, match)
        response['data'] = {
            'participants': match.participants.count(),
        }
        return JsonResponse(response)

class RoundResultsJSON(LoginRequiredMixin, View):
    model = Match
    
    def get(self, request, pk, round_order):
        response = {}
        
        try:
            match = self.model.objects.get(pk=pk)
            results = match.get_round_results(round_order)
        except Exception as e:
            response['success'] = 'false'
            response['message'] = str(e)  
            response['data'] = {}          
            return JsonResponse(response)
        
    
        response['success'] = 'true'
        response['data'] = results        
        return JsonResponse(response)
    
class MatchDetailJSON(LoginRequiredMixin, View):
    model = Match
    
    def get(self, request, pk):
        response = {}
        
        try:
            match = self.model.objects.get(pk=pk)                
        except Exception as e:
            response['success'] = 'false'
            response['message'] = str(e)  
            response['data'] = {}          
            return JsonResponse(response)
        
        data = match.serialize()        
        
        teams = []
        rounds = match.rounds.all()
        drafts = match.drafts.all()
        if drafts.count():
            for d in drafts:
                teams.append(d)
        elif rounds.count() > 0:
            for r in rounds:
                teams.append(r.attackers)
                teams.append(r.defenders)
                
            last_round = rounds.last()
            data['prev_att'] = last_round.attackers.serialize()
            data['prev_def'] = last_round.defenders.serialize()
            
        data['teams'] = [t.serialize() for t in set(teams)]
        data['roles'] = [r.serialize() for r in Role.objects.all()]
        data['maps'] = [m.serialize() for m in Map.objects.all()]
    
        response['success'] = 'true'
        response['data'] = data      
        return JsonResponse(response)

class AddRound(LoginRequiredMixin, View):
    model = RoundSession    
    players_q = Player.objects.all()
    roles_q   = Role.objects.all()
    
    def create_player_session(self, player, team, session):
        p = self.players_q.get(pk=int(player['player']))
        r = self.roles_q.get(pk=int(player['role']))
        k = int(player['kills'])
        d = int(player['deaths'])
        PlayerSession.objects.create(player=p,
                                    role=r,
                                    round_session=session,
                                    kills=k,
                                    deaths=d,
                                    team=team)
        
        
    
    # ADD ROUND - Accepts JSON
    def post(self, request, pk):
        if not request.content_type == 'application/json':
            return JsonResponse({
                'success': 'false',
                'message': 'This endpoint accepts only json content type',
                }, status=400)
        
        data = json.loads(request.body)
        if not data:
            return JsonResponse({
                'success': 'false',
                'message': 'No data were sent',
                }, status=400)
        
        try:
            round_ord       = int(data['order']) or 1
            _map            = int(data['mapa'])
            round_dur       = int(data['duration'])
            round_mcoms     = int(data['mcomsDestroyed'])
            
            team_att        = int(data["team[0]"]) if data["team[0]"] else None
            team_def        = int(data["team[1]"]) if data["team[1]"] else None
            
            leader_att      = int(data['attackers']['leader'])
            leader_def      = int(data['defenders']['leader'])
            
            players_att     = data['attackers']['players']
            players_def     = data['defenders']['players']
        except (KeyError, IndexError) as e:
            return JsonResponse({
                'success': 'false',
                'message': str(e),
                }, status=400)
        
        # start quering db
        try:
            match     = Match.objects.get(pk=pk)
            if match.rounds.count() > round_ord:
                round_ord = match.rounds.count() + 1
            round_map = Map.objects.get(pk=_map)
            
            round_ses = RoundSession.objects.create(map=round_map,
                                                    duration=round_dur,
                                                    mcoms_destroyed=round_mcoms,
                                                    order=round_ord,
                                                    match=match)        

            if team_att is not None and Team.objects.filter(pk=team_att).exists():
                attackers = Team.objects.get(pk=team_att)
            else:              
                attackers = (Team.objects.create(leader=Player.objects
                                                    .get(pk=leader_att)))
                
            if team_def is not None and Team.objects.filter(pk=team_def).exists():
                defenders = Team.objects.get(pk=team_def)
            else:
                defenders = (Team.objects.create(leader=Player.objects
                                                    .get(pk=leader_def)))

            for player in players_att:
                self.create_player_session(player, attackers, round_ses)

            for player in players_def:
                self.create_player_session(player, defenders, round_ses)

            round_ses.attackers = attackers
            round_ses.defenders = defenders

            round_ses.save()
            
            
        except Exception as e:
            return JsonResponse({
                'success': 'false',
                'message': str(e),
                }, status=400)
        
        
        
        return JsonResponse({'success': 'true'})
    
class MatchesUpdate(LoginRequiredMixin, View):
    model = Match
    template = "matches/match_form.html"    
    fields = ['title', 'start_at', 'description', 'completed', 'maps', 'leaders', 'game', 'participants']


    def get(self, request, pk):
        match = get_object_or_404(self.model, pk=pk)
        form = MatchCreateForm(instance=match)
        ctx = {'form': form}
        return render(request, self.template, ctx)
    
    def post(self, request, pk):
        match = get_object_or_404(self.model, pk=pk)    
        form = MatchCreateForm(request.POST, instance=match)
        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template, ctx)
        print(form.cleaned_data)
        form.save()
        
        return redirect(reverse_lazy('matches:match-list'))