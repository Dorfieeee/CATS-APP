from itertools import chain
import json
from django.utils import timezone
from django.db import models
from myapp.settings import AUTH_USER_MODEL

def sort_by_points(e):
    return e['points']
  
class Game(models.Model):
    name = models.CharField(max_length=64)
    image = models.URLField('Img source url')
    
    def serialize(self):
        return {
            'game_pk': self.pk,
            'name': self.name,
            'image': self.image,
        }
    
    def __str__(self):
        return self.name


class Map(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=16)
    mcoms = models.PositiveSmallIntegerField()
    has_skyfall = models.BooleanField()
    
    def serialize(self):
        return {
            'map_pk': self.pk,
            'name': self.name,
            'code': self.code,
            'mcoms': self.mcoms,
            'has_skyfall': self.has_skyfall,
            'image': self.img,
            'size': self.size,
        }
    
    @property
    def img(self):
        if self.code:
            return 'https://cdn.battlelog.com/bl-cdn' + \
                       '/cdnprefix/1715536/public/base/bf4' + \
                       '/map_images/335x160/%s.jpg' % self.code
                       
        return 'https://tl.net/tlpd/images/maps/unknown.jpg'
    
    @property
    def size(self):
        if self.mcoms <= 6:
            return 'small'
        elif self.mcoms <= 8:
            return 'medium'
        else:
            return 'large'
   
    def __str__(self):
        return self.name


class Participant(models.Model):
    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    match = models.ForeignKey('Match', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return '%s->%s#%s' % (self.player.user.username, self.match.title, self.match.pk)
    
    class Meta:
        unique_together = ['player', 'match']
  
        
class Match(models.Model):
    title = models.CharField(max_length=32)
    start_at = models.DateTimeField()
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    leaders = models.ManyToManyField('Player', related_name='leaders', through='MatchLeader')
    maps = models.ManyToManyField('Map', related_name='maps', through='MatchMap')
    participants = models.ManyToManyField('Player', related_name='participates_in',
                                          through=Participant)
    
    
    def serialize(self):
        return {
            'match_pk': self.pk,
            'title': self.title,
            'start_at': self.start_at,
            'description': self.description,
            'completed': self.completed,
            'drafts': [d.serialize() for d in self.drafts.all()],
            'game': self.game.serialize(),
            'participants': [p.serialize() for p in self.participants.all()],
            'participants_count': self.participants.count(),
            'rounds_count': self.rounds.count(),
        }
    
    class Meta:
        ordering = ['-start_at']
    
    def save(self, *args, **kwargs):
        # TODO
        # m2m error, cannot check leaders before self exists
        # if self.leaders.count() > 2:
        #     raise Exception('Zapas nemuze mit vice jak 2 velitele')            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return "%s#%s" % (self.title, self.pk)
    
    def is_past_start(self):
        return timezone.now() > self.start_at
    

    def add_player(self, member):
        try:
            player = member.players.get(game=self.game)
        except:
            raise Exception('%s does not have player for %s' % \
                            (member, self.game))
        if player in self.participants.all():
            raise Exception('%s is already participating' % player)
        self.participants.add(player)

    def remove_player(self, member):
        try:
            player = member.players.get(game=self.game)
        except:
            raise Exception('%s does not have player for %s' % \
                            (member, self.game))
        if player not in self.participants.all():
            raise Exception('%s is not yet participating' % player)
        self.participants.remove(player)
    
    def get_players_results(self):        
        results = []
        sessions = PlayerSession.objects.filter(round_session__match=self.pk)
        players = self.participants.all()
        totals = (sessions.values('player')
                            .annotate(kills=models.Sum('kills'),
                                        deaths=models.Sum('deaths'))
                            .order_by('-kills'))
        
        for ses in totals:
            stats = {
                'kd': 0,
                'kd_delta': 0,                
                'kpm': 0,         
                'kpm_delta': 0,    
            }
            playtime = sum([s.round_session.duration for 
                            s in sessions.filter(player__pk=ses['player'])])
            
            player = players.get(pk=ses['player'])
            
            prev_stats = player.get_stats(before=self.start_at)
            
            stats['player'] = player
            stats['kills'] = ses['kills']
            stats['deaths'] = ses['deaths']
            
            if ses['deaths'] > 0:
                stats['kd'] = round(ses['kills'] / ses['deaths'], 2)
            else:
                stats['kd'] = ses['kills']
                
            if prev_stats['kd'] > 0:
                stats['kd_delta'] = round(stats['kd'] - prev_stats['kd'], 2)
            
            if playtime > 0:
                stats['kpm'] = round(ses['kills'] / playtime, 2)
                
            if prev_stats['kpm'] > 0:
                stats['kpm_delta'] = round(stats['kpm'] - prev_stats['kpm'], 2)

            results.append(stats)
        
        return results

    def get_round_results(self, round_order):
        results = {
            'attackers': {
                    'players': [],
                },
            'defenders': {
                    'players': [],
                },
            'round': '',
            'map': '',
            'winner': '',
            'mcoms_destroyed': '',
        }
        
        try:
            r = RoundSession.objects.get(match=self.pk, order=round_order)
        except:
            raise Exception('Round #%s @ %s not found' % (round_order, self))
        
        sessions = r.players.all()
        totals = (sessions.values('player', 'team').annotate(kills=models.Sum('kills'),deaths=models.Sum('deaths')).order_by('-kills'))
        
        for record in totals:
            stats = {
                'kd': 0,
                'kd_delta': 0,                
                'kpm': 0,         
                'kpm_delta': 0,  
            }
            playtime = r.duration
            
            player_session = sessions.get(player=record['player'])
            player = player_session.player
            prev_stats = player.get_stats(before=self.start_at)
            
            stats['user'] = player.user.serialize()
            stats['role'] = player_session.role.serialize()
            stats['kills'] = record['kills']
            stats['deaths'] = record['deaths']
            
            if record['deaths'] > 0:
                stats['kd'] = round(record['kills'] / record['deaths'], 2)
            else:
                stats['kd'] = record['kills']
                
            if prev_stats['kd'] > 0:
                stats['kd_delta'] = round(stats['kd'] - prev_stats['kd'], 2)
            
            if playtime > 0:
                stats['kpm'] = round(record['kills'] / playtime, 2)
                
            if prev_stats['kpm'] > 0:
                stats['kpm_delta'] = round(stats['kpm'] - prev_stats['kpm'], 2)
                
            if record['team'] == r.attackers.pk:
                results['attackers']['players'].append(stats)
            else:
                results['defenders']['players'].append(stats)
        
        results['defenders']['leader'] = r.defenders.leader.user.serialize()
        results['defenders']['team'] = r.defenders.pk
        results['attackers']['leader'] = r.attackers.leader.user.serialize()
        results['attackers']['team'] = r.attackers.pk
        results['round'] = r.pk
        results['map'] = r.map.serialize()
        if r.all_mcoms_destroyed:
            results['winner'] = r.attackers.pk
        else:
            results['winner'] = r.defenders.pk
        results['mcoms_destroyed'] = r.mcoms_destroyed
        
        json.dumps(results)
        
        return results

    @property
    def results(self):
        leaders = self.leaders.all()
        
        if not leaders.count() == 2: return
        
        result = {
            'leaders': [],
            'winner': None,
        }
        
        for leader in leaders:
            result['leaders'].append({
                'player': leader,
                'points': 0,
                'mcoms_destroyed': 0,
            })
        
        rounds = self.rounds.all()
        
        for r in rounds:
            winner = r.winner.leader
            for leader in result['leaders']:                
                # Add one point if leader won the round
                if winner == leader['player']:
                    leader['points'] = leader['points'] + 1
                # Add points for destroyed mcoms to attacking team
                if leader['player'] == r.attackers.leader:
                    leader['mcoms_destroyed'] = \
                        leader['mcoms_destroyed'] + r.mcoms_destroyed     
        
        # If leader has more points => winner, opposite loser, otherwise
        # no changes made => draw
        if result['leaders'][0]['points'] > result['leaders'][1]['points']:
            result['winner'] = result['leaders'][0]['player']
            result['loser'] = result['leaders'][1]['player']
        elif result['leaders'][0]['points'] < result['leaders'][1]['points']:
            result['winner'] = result['leaders'][1]['player']
            result['loser'] = result['leaders'][0]['player']

        # let winner be always the first in the list
        result['leaders'].sort(key=sort_by_points, reverse=True)
        
        result['mcoms'] = "%s : %s" % (result['leaders'][0]['mcoms_destroyed'],
                                     result['leaders'][1]['mcoms_destroyed'])
        
        return result
        


class Role(models.Model):
    '''
    Utocnik, Kulometcik, Sniper...
    '''
    name = models.CharField(max_length=32)
    icon_name = models.CharField('FontAwesome icon name',max_length=32)
    
    def serialize(self):
        return {
            'role_pk': self.pk,
            'name': self.name,
            'fa-icon': self.icon_name,
        }
    
    def __str__(self):
        return self.name
           
        
class Player(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='players')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    # other attributes
    
    def serialize(self):
        return {
            'player_pk': self.pk,
            'name': self.user.username,
        }
    
    # methods for calculating stats? get_kills_count, get_deaths_count, KD, KPM...
    # get_stats_per_round, get_stats_per_match
    # unique together [user, game]
    
    def __str__(self):
        return self.user.__str__()
    
    # Get stats for most recent "number_of_matches"
    # Excluded
    def get_stats(self, number_of_matches=15, exclude=[],
                  *args, **kwargs):
        '''
        Get stats for most recent number_of_matches -> int
        \n
        Default is 15
        \n
        Can exclude some matches from the query by their PK
        - exclude matches won't be taken out from the recent pool
        \n
        exclude -> int or list[int]
        \n
        If date is provided, it excludes any Match which started later
        '''
        if 'before' in kwargs:
            date = kwargs['before']
        
        if exclude and type(exclude) == int:
            exclude = [exclude]   # if a single digit, make it a list
        
        stats = {
                'player': self,                
                'kills': 0,                
                'deaths': 0,    
                'kd': 0,
                'kpm': 0,     
            }       
        
        
        # Player -> PlayerSessions -> Exclude
        recent_matches = (self.participates_in
                                  .exclude(pk__in=exclude,
                                           completed=False))
        if 'before' in kwargs:
            recent_matches = recent_matches.exclude(start_at__gte=date)           
        
        recent_matches = recent_matches[:number_of_matches]
        
        sessions = (self.sessions_played
                        .filter(round_session__match_id__in=recent_matches))
        
        # If empty query - Player does not have any records
        if not sessions:
            return stats
        
        totals = (sessions.values('player')
                          .annotate(kills=models.Sum('kills'),
                                    deaths=models.Sum('deaths')))[0]

        playtime = sum([s.round_session.duration for s in self.sessions_played.all()])

        stats['kills'] = totals['kills']
        stats['deaths'] = totals['deaths']
        
        if totals['deaths'] != 0:
            stats['kd'] = round(totals['kills'] / totals['deaths'], 2)
          
        if playtime != 0:  
            stats['kpm'] = round(totals['kills'] / playtime, 2)
        

        return stats      


class Team(models.Model):
    leader = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='team_leader')
    name = models.CharField(max_length=32, null=True, blank=True)
    created = models.DateField(auto_now_add=True)
    
    def serialize(self):
        # get unique Players which have PlayerSession with this Team
        players = Player.objects.filter(sessions_played__team=self).distinct()
        return {
            'pk': self.pk,
            'leader': self.leader.serialize(),
            'players': [p.serialize() for p in players],
            'name': str(self.leader) + "#" + str(self.pk),
        }
    
    # add methods to sum players kills and deaths?
    def __str__(self):
        if self.name: return self.name
        return "%s# %s @ %s/%s" % (self.pk, self.leader, self.created.day, self.created.month)   
   

class TeamDraft(models.Model):
    leader = models.ForeignKey(Player, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    players = models.ManyToManyField(Player, related_name='drafted_in')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='drafts')
    created = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.name + self.created.strftime("(%d-%m)")
    
    def serialize(self):
        return {
            'pk': self.pk,
            'leader': self.leader.serialize(),
            'players': [p.serialize() for p in self.players.all()],
            'name': self.__str__(),
        }
    

class PlayerSession(models.Model):
    kills = models.PositiveSmallIntegerField()
    deaths = models.PositiveSmallIntegerField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sessions_played')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, related_name='role',
                             default=1, null=True)
    round_session = models.ForeignKey('matches.RoundSession', on_delete=models.CASCADE,
                                    related_name='players')
    
    def serialize(self):
        return {
            'player_pk': self.player.pk,
            'kills': self.kills,
            'deaths': self.deaths,
            'role': self.role.serialize(),
            'team_pk': self.team.pk,
            'roun_pk': self.round_session.pk,
        }
    
    def __str__(self):
        return self.player.__str__()
    
    class Meta:
        unique_together = ['player', 'round_session', 'team']

    
class RoundSession(models.Model):
    # Map played
    map = models.ForeignKey(Map, on_delete=models.SET_NULL, null=True)
    # Order no. of round in a match
    order = models.PositiveSmallIntegerField(default=1)
    screenshot = models.URLField(blank=True, null=True) # change to ImageField /scr/match.id/round.order
    # Teams
    attackers = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name='attackers')
    defenders = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name='defenders')
    # Outcome
    duration = models.PositiveIntegerField(verbose_name='Duration in minutes', default=0)
    mcoms_destroyed = models.PositiveSmallIntegerField(default=0)
    
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='rounds')
    
    def serialize(self):        
        return {
            'rsession_pk': self.pk,
            'map': self.map.serialize(),
            'order': self.order,
            'screenshot': self.screenshot,
            'attackers_pk': self.attackers.pk,
            'defenders_pk': self.defenders.pk,
            'duration': self.duration,
            'mcoms_destroyed': self.mcoms_destroyed,
            'match_pk': self.match.pk,
            'winner_pk': self.get_winner_team().pk,
        }    

    @property    
    def winner(self):
        if self.all_mcoms_destroyed:
            return self.attackers
        return self.defenders
    
    def get_winner_team(self):
        if self.all_mcoms_destroyed:
            return {
                'side': 'Útočníci',
                'team': self.attackers,
                'leader': self.attackers.leader,
            }
        else:
            return {
                'side': 'Obránci',
                'team': self.defenders,
                'leader': self.defenders.leader,
            }
            
    @property
    def all_mcoms_destroyed(self):
        '''
        Att team won -> True, otherwise Def team did
        '''
        return (self.map.mcoms - self.mcoms_destroyed) == 0
    
    def __str__(self):
        return 'Round %s of %s' % (self.order, self.match)

    class Meta:
        unique_together = ['match', 'order']
    
    def save(self, *args, **kwargs):
        if self.attackers is not None and self.defenders is not None:
            if self.attackers == self.defenders:
                raise Exception('Attackers and defenders cannot be the same teams')
            
        super().save(*args, **kwargs)
  
  
class MatchMap(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    
    def __str__(self):
        return '%s played in %s#%s' % (self.map.name, self.match.title, self.match.pk)


class MatchLeader(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)      
    match = models.ForeignKey(Match, on_delete=models.CASCADE)   
       
    def __str__(self):
        return '%s as leader in %s#%s' % (self.player.user.username, self.match.title, self.match.pk)

