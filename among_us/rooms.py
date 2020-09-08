import mud
from . import items, actions
import dib
import random

class Room(mud.Area):
    def full_desc(self,player):
        base=super().full_desc(player)
        if self.links:
            if len(self.links)>1:
                return base+" There are doors to the %s." % dib.smart_list(list(self.links.keys()))
            else:
                return base+" There is a door to the %s." % list(self.links.keys())[0]
        return base+" There are no doors here. How did you get in?!"
    async def activate(self,game:mud.MUD):
        #return true if something happened
        pass
    async def sabotage(self,game:mud.MUD):
        pass
class Cabins(Room):
    name = "Cabins"
    desc = "This is where you woke up."

class Armoury(Room):
    name="Armoury"
    desc = "The weapons room."
    def __init__(self):
        super().__init__()
        self.entities.extend([items.Pistol(),items.Pistol(),items.Pistol()])

class Bridge(Room):
    name="Bridge"
    desc = "The helm of the ship. You can make ship-wide announcements here."
    special_actions = [actions.Broadcast]

class Airlock(Room):
    name="Airlock"
    desc="Activate this to void any items or players inside to space!"
    special_actions = [actions.Activate]
    async def activate(self,game:mud.MUD):
        for p in game.players:
            if p.area is self:
                await p.dm("You are suddenly ejected into space!")
                await game.kill(p,"asphyxiated")
        self.entities=[]
        return True

class Morgue(Room):
    name="Morgue"
    desc="Where dead bodies are supposed to go."

class Office(Room):
    name="Office"
    desc="Where important people work."
    def __init__(self):
        super().__init__()
        self.entities.append(items.Documents())

class Security(Room):
    name="Security"
    desc = "You can view where everyone is here."
    special_actions = [actions.Cameras]

class Storage(Room):
    poss_items=[items.DnD,items.Paper,items.CaptainLaptop,items.Pistol,items.Crisps]
    name="Storage Room"
    desc="Filled with various junk."
    def __init__(self):
        super().__init__()
        for c in random.choices(self.poss_items,k=3):
            self.entities.append(c())

all_rooms=[Armoury,Bridge,Airlock,Morgue,Office,Security,Storage]