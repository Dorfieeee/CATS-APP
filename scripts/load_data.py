from ucet.models import Member
from matches.models import Map, Player, Game, Role
from myapp.settings import BASE_DIR
import os
import json
import datetime
import csv

def log(content, success=True):
    if success:
        msg = '\033[92m✓ - %s\033[00m' % content
    else:
        msg = '\033[91m❌ - %s\033[00m' % content
    print(msg)
    
def run():         
        
    print('Loading games...')   
    bf4 = Game(
        name='Battlefield 4',
        image='https://d34ymitoc1pg7m.cloudfront.net/common/menu/section-select-bf4-56d900fe.jpg'
        )
    bf4.save()
    log('Games uploaded')
    
    
    print('Loading maps...')    
    with open(os.path.join(BASE_DIR, 'scripts', 'maps.csv'), 'r', newline='') as f:
        maps = csv.DictReader(f)
        for map in maps:
            
            mcoms = int(map['mcoms'])
            has_skyfall = bool(int(map['has_skyfall']))
            
            Map.objects.get_or_create(
                name=map['name'],
                code=map['code'],
                mcoms=mcoms,
                has_skyfall=has_skyfall,
            )
        log('Maps uploaded')
        
    print('Loading roles...') 
    Role.objects.create(name="Útočník", icon_name="medkit")
    Role.objects.create(name="Sniper", icon_name="crosshairs")
    Role.objects.create(name="Radista", icon_name="wifi")
    log('Roles uploaded')
    
    print('Loading users...')
    with open(os.path.join(BASE_DIR, 'scripts', 'members.json'), 'r') as f:
        members = json.loads(f.read())
        current_members = Member.objects.all()
        _member = None
        for member in members:
            try:
                _member = current_members.get(discord_id=member['id'])
            except Member.DoesNotExist:            
                # '2021-04-22T19:20:25.942Z' -> replace Z to create ISO format with TZ
                joined_at = datetime.datetime.fromisoformat(member['joined_at'].replace('Z','+00:00'))          
                _member = Member(
                    discord_id = member['id'],
                    username = member['username'],
                    avatar = member['avatar'],
                    roles = ','.join(member['roles']),
                    joined_at = joined_at,
                )            
                _member.save()  

            Player.objects.get_or_create(user=_member, game=bf4)
                                  
        log('Users uploaded and BF4 player init for each')
        
        
    print('Creating admin...')
    try:
        dorf = Member.objects.get(discord_id='487532180223033354')
        dorf.is_staff = True
        dorf.is_superuser = True
        dorf.save()
        log('Admin %s created' % dorf.username)
    except Member.DoesNotExist:
        log('Admin could not be set', success=False)
    