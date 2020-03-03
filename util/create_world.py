from django.contrib.auth.models import User
from adventure.models import Player, Room, RoomGenerator, Map

Room.objects.all().delete()
world_map = RoomGenerator(4).make_map()

players = Player.objects.all()

for p in players:
    p.currentRoom = world_map.rooms[0].id
    p.save()
