from .game import *
from .werewolf import Werewolf,Seer

class AlphaWolf(Werewolf):
    transform = None
    singleton = True
    desc = "You get to transform someone into a werewolf during the night! However, you can't look for love :("
    async def setup(self,game:OneNight):
        await game.send("Alpha Wolf present, center card 2 replaced with Werewolf!")
        game.center[2]=Werewolf(None)
    async def preload(self,game:OneNight):
        await self.user.dm("Choose a player to make a werewolf!")
        self.transform = await game.dm_tag(self.user,game.other_players(self.user))
    async def execute(self, game: OneNight, phase):
        await super().execute(game,phase)
        game.swap_roles(2,self.transform)
        game.history.append(f"{self.user.name} swapped {self.transform.name} with center card 2, making them a {self.transform.role.name}!")
class MysticWolf(Werewolf):
    desc = "You're a Werewolf who also gets to view another person's role"
    choice = None
    phases = [Werewolf.phase,Seer.phase]
    async def preload(self,game:OneNight):
        await super().preload(game)
        await self.user.dm("Choose a player to look at!")
        self.choice = await game.dm_tag(self.user, game.other_players(self.user))
    async def execute(self, game: OneNight, phase):
        if phase==Werewolf.phase:
            await super().execute(game,phase)
        else:
            await self.user.dm(f"Target's role is {self.choice.role.name}!")
            game.history.append(f"{self.user.name} divined {self.choice.name}'s role, and saw a {self.choice.role.name}.")
class DreamWolf(EvilRole):
    desc = "You're a Werewolf, but you're lazy and can't be bothered to get up during the night (The other werewolves still know who you are)"
    team = "werewolf"
class Witch(Village):
    desc = "You look at a center card, then swap it with any player (including you!)"
    phase = 5.1
    singleton = True
    async def execute(self, game: OneNight, phase:float):
        looking = await game.choose_number(self.user,True,1,3,"Choose a center card to look at.")
        crole = game.center[looking]
        await self.user.dm(f"You saw a {crole.name}! Who do you want to switch it with?")
        switch = await game.dm_tag(self.user,game.players)
        game.swap_roles(switch,looking)
        game.history.append(f"{self.user.name} looked at center card {looking} ({crole.name}), and then swapped it with {switch.name}.")
class Revealer(Village):
    desc = "You get to look at another player's card, revealing it to everyone if they're on the village team."
    revealing = None
    phase = 10
    singleton = True
    async def preload(self,game:OneNight):
        await self.user.dm("Choose a player to reveal!")
        self.revealing = await game.dm_tag(self.user, game.other_players(self.user))
    async def execute(self, game: OneNight, phase:float):
        revealed = self.revealing.role
        await self.user.dm(f"{self.revealing.name} is a {revealed.name}!")
        if revealed.team=="village":
            await game.send(f"{self.revealing.name} has been revealed to be a {revealed.name}!")
        game.history.append(f"{self.user.name} revealed {self.revealing.name}, who was a {revealed.name}.")
roles = [AlphaWolf,MysticWolf,DreamWolf,Witch,Revealer]