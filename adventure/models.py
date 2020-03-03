from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import uuid
import math
import random


class Room(models.Model):
    title = models.CharField(max_length=50, default="DEFAULT TITLE")
    description = models.CharField(max_length=500, default="DEFAULT DESCRIPTION")
    n_to = models.IntegerField(default=0)
    s_to = models.IntegerField(default=0)
    e_to = models.IntegerField(default=0)
    w_to = models.IntegerField(default=0)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    asset = models.CharField(max_length=50, default="")

    def connectRooms(self, destinationRoom, direction):
        destinationRoomID = destinationRoom.id
        try:
            destinationRoom = Room.objects.get(id=destinationRoomID)
        except Room.DoesNotExist:
            print("That room does not exist")
        else:
            if direction == "n":
                self.n_to = destinationRoomID
            elif direction == "s":
                self.s_to = destinationRoomID
            elif direction == "e":
                self.e_to = destinationRoomID
            elif direction == "w":
                self.w_to = destinationRoomID
            else:
                print("Invalid direction")
                return
            self.save()

    def playerNames(self, currentPlayerID):
        return [p.user.username for p in Player.objects.filter(currentRoom=self.id) if p.id != int(currentPlayerID)]

    def playerUUIDs(self, currentPlayerID):
        return [p.uuid for p in Player.objects.filter(currentRoom=self.id) if p.id != int(currentPlayerID)]

    def get_coordinates(self):
        return self.x, self.y


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    currentRoom = models.IntegerField(default=0)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    def initialize(self):
        if self.currentRoom == 0:
            self.currentRoom = Room.objects.first().id
            self.save()

    def room(self):
        try:
            return Room.objects.get(id=self.currentRoom)
        except Room.DoesNotExist:
            self.initialize()
            return self.room()


class Map:
    def __init__(self, rooms):
        self.rooms = rooms
        self.size = math.sqrt(len(rooms))


class DisjointSet:
    def __init__(self, elements):
        self._set = {}
        for element in elements:
            self._set[element] = element

    def find(self, element):
        if self._set[element] == element:
            return element
        else:
            return self.find(self._set[element])

    def union(self, element1, element2):
        _set1 = self.find(element1)
        _set2 = self.find(element2)
        self._set[_set1] = _set2


class RoomGenerator:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.adj_list = dict()
        self.rooms = [0] * grid_size

        for i in range(grid_size):
            self.rooms[i] = [None] * grid_size
            for z in range(0, len(self.rooms[i])):
                self.rooms[i][z] = Room()

        for x in range(0, grid_size):
            for y in range(0, grid_size):
                self.rooms[x][y].x = x
                self.rooms[x][y].y = y
                self.rooms[x][y].save()
                node = (x, y)
                self.adj_list[node] = list()

        for node in self.adj_list.keys():
            x, y = node
            neighbours = list()
            if x > 0:
                neighbours.append((x - 1, y))
            if x < grid_size - 1:
                neighbours.append((x + 1, y))
            if y > 0:
                neighbours.append((x, y - 1))
            if y < grid_size - 1:
                neighbours.append((x, y + 1))
            self.adj_list[node] = neighbours

    def make_map(self):
        print("making map")
        return Map(self.set_rooms())

    def set_rooms(self):
        print("setting rooms")
        counter = 0
        for i in self.spanning_tree_using_kruskal():
            x1 = i[0][0]
            y1 = i[0][1]
            x2 = i[1][0]
            y2 = i[1][1]
            room1 = self.rooms[x1][y1]
            room2 = self.rooms[x2][y2]
            if x1 == x2:
                if y1 < y2:
                    room1.e_to = room2.id
                    room2.w_to = room1.id
                else:
                    room1.w_to = room2.id
                    room2.e_to = room1.id
            elif x1 < x2:
                room1.s_to = room2.id
                room2.n_to = room1.id
            else:
                room1.n_to = room2.id
                room2.s_to = room1.id
                self.asset = ""
        flat_rooms = []
        for rooms in self.rooms:
            flat_rooms += rooms

        for i in flat_rooms:
            if i.n_to != 0:
                i.asset += "n"
            if i.s_to != 0:
                i.asset += "s"
            if i.e_to != 0:
                i.asset += "e"
            if i.w_to != 0:
                i.asset += "w"
            i.asset += "_1.tmx"
            i.save()
        print("rooms set")
        print(type(flat_rooms))
        return flat_rooms

    def spanning_tree_using_kruskal(self):
        tree_edges = list()
        graph_edges = list()
        for node in self.adj_list.keys():
            neighbours = self.adj_list[node]
            for neighbour in neighbours:
                if ((node, neighbour) not in graph_edges and
                        (neighbour, node) not in graph_edges):
                    graph_edges.append((node, neighbour))
        disjoint_set = DisjointSet(self.adj_list.keys())
        while len(tree_edges) < (len(self.adj_list.keys()) - 1):
            rnd_edge = random.choice(graph_edges)
            node1, node2 = rnd_edge
            set1 = disjoint_set.find(node1)
            set2 = disjoint_set.find(node2)
            if (set1 != set2):
                disjoint_set.union(node1, node2)
                tree_edges.append(rnd_edge)
            graph_edges.remove(rnd_edge)
        return tree_edges


@receiver(post_save, sender=User)
def create_user_player(sender, instance, created, **kwargs):
    if created:
        Player.objects.create(user=instance)
        Token.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_player(sender, instance, **kwargs):
    instance.player.save()
