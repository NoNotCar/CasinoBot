from .game import *

class Tanner(Role):
    team = "tanner"
    desc = "You hate your job! Act suspiciously and get yourself killed!"
    def did_win(self,game:OneNight,player:ONP):
        return player.dead
class Hunter(Village):
    desc = "If you die, whoever you voted for also dies."
    async def on_death(self,game:OneNight,player:ONP):
        if await game.kill(player.voted_for):
            await game.send(f"{player.name} was a Hunter, and shot {player.voted_for.name}!")
class Werewolf(EvilRole):
    team = "werewolf"
    center = 0
    phase = 2
    desc = "You're a werewolf! Pretend you're a villager!"
    async def preload(self,game:OneNight):
        self.center = await game.choose_number(self.user,True,1,3,"Choose a center card to look at, for the case where you're a lonely werewolf looking for love.")
    async def execute(self, game: OneNight, phase):
        werewolves = [p for p in game.players if p!=self.user and p.start_role.team==self.team]
        if werewolves:
            await self.user.dm(f"AWOOO! Your fellow werewolves are: {dib.smart_list([w.name for w in werewolves])}")
        elif self.center:
            await self.user.dm(f"Oh no! You're a single werewolf, and you see a {game.center[self.center].name} while looking for love.")
            game.history.append(f"{self.user.name} was a single werewolf, and saw a {game.center[self.center].name}.")

class Mason(Village):
    phase = 3
    desc = "Being a mason, you know exactly who your fellow masons are."
    async def execute(self, game: OneNight, phase):
        masons = [p for p in game.players if p!=self.user and isinstance(p.start_role,Mason)]
        if masons:
            names = dib.smart_list([m.name for m in masons])
            await self.user.dm(f"Your fellow mason(s) are: {names}")
            game.history.append(f"{self.user.name} saw {names} were masons")
        else:
            await self.user.dm("Oh no, you have no other masons to back you up! :(")
            game.history.append(f"{self.user.name} saw no other masons.")
    @classmethod
    def set_valid(cls, rset: typing.List[typing.Type[Role]], final:bool):
        return not final or rset.count(Mason)>1
class Seer(Village):
    phase = 4
    desc = "During the night, you may see either two cards from the center or another player's role"
    choice = None
    async def preload(self,game:OneNight):
        if await game.yn_option(self.user,True,"Look at a card from the center during the night?"):
            self.choice = await game.choose_number(self.user,True,1,3,"Choose which card _not_ to look at.")
        else:
            await self.user.dm("Choose someone to target!")
            self.choice = await game.dm_tag(self.user,[p for p in game.players if p!=self.user])
    async def execute(self, game: OneNight, phase):
        if isinstance(self.choice,ONP):
            await self.user.dm(f"Target's role is {self.choice.role.name}!")
            game.history.append(f"{self.user.name} looked at {self.choice.name}'s role, and saw a {self.choice.role.name}.")
        elif isinstance(self.choice,int):
            actual = [n for n in range(1,4) if n!=self.choice]
            names = dib.smart_list([game.center[a].name for a in actual])
            await self.user.dm(f"Saw {names} in the center! (in increasing numerical order)")
            game.history.append(f"{self.user.name} saw {names} in the center.")
class Robber(Village):
    phase = 5
    desc = "You steal another player's role during the night and look at it."
    target = None
    singleton = True
    async def preload(self,game:OneNight):
        await self.user.dm("Choose a player to steal from!")
        self.target = await game.dm_tag(self.user,[p for p in game.players if p!=self.user])
    async def execute(self, game: OneNight, phase):
        game.swap_roles(self.user,self.target)
        await self.user.dm(f"You stole a {self.user.role.name}!")
        game.history.append(f"{self.user.name} stole {self.user.role.name} from {self.target.name}, giving them the {self.target.role.name}.")
class Troublemaker(Village):
    phase = 6
    desc = "You swap two other player's roles around."
    target1 = None
    target2 = None
    singleton = True
    async def preload(self,game:OneNight):
        await self.user.dm("Choose your first victim!")
        self.target1 = await game.dm_tag(self.user, [p for p in game.players if p != self.user])
        await self.user.dm("Choose your second victim!")
        self.target2 = await game.dm_tag(self.user, [p for p in game.players if p != self.user and p !=self.target1])
    async def execute(self, game: OneNight, phase):
        game.swap_roles(self.target1,self.target2)
        game.history.append(f"{self.user.name} swapped {self.target1.name} and {self.target2.name}'s roles, leaving them with the {self.target1.role.name} and {self.target2.role.name}.")
class Drunk(Village):
    phase = 7
    desc = "You swap your card with a center card."
    choice = 0
    singleton = True
    async def preload(self,game:OneNight):
        self.choice = await game.choose_number(self.user,True,1,3,"Choose a card to drink!")
    async def execute(self, game: OneNight, phase):
        game.swap_roles(self.user,self.choice)
        game.history.append(f"{self.user.name} drank center card {self.choice}, becoming the {self.user.role.name}")
class Insomniac(Village):
    phase = 9
    desc = "At the end of the night, you look at your own role."
    async def execute(self, game: OneNight, phase):
        await self.user.dm(f"You are now the {self.user.role.name}!")
        game.history.append(f"{self.user.name} woke up and found out they were the {self.user.role.name}")
from .daybreak import Revealer
from .darkside import Cockerel
class DoppelGanger(Role):
    desc = "You copy someone else's role at the start of the night."
    singleton = True
    copied_role = None
    special_phases = {9:Insomniac,10.5:Revealer,9.1:Cockerel}
    async def preload(self,game:OneNight):
        target = await game.dm_tag(self.user,[p for p in game.players if p!=self.user])
        self.copied_role=target.role.__class__(self.user)
        self.team=self.copied_role.team
        self.evil = self.copied_role.evil
        await self.user.dm(f"You copied the {self.copied_role.name}!")
        game.history.append(f"{self.user.name} doppelganged {target.name}, who was a {self.copied_role.name}.")
        await self.copied_role.preload(game)
    async def execute(self, game: OneNight, phase:float):
        if role:=self.special_phases.get(phase,None):
            if isinstance(self.copied_role,role):
                await self.copied_role.execute(game,phase)
    async def on_death(self,game:OneNight,player:ONP):
        await self.copied_role.on_death(game,player)
    def did_win(self,game:OneNight,player:ONP):
        return self.copied_role.did_win(game,player)
    @property
    def phases(self) ->typing.List[int]:
        return [1]+list(self.special_phases.keys())
roles = [DoppelGanger,Werewolf,Mason,Seer,Robber,Troublemaker,Drunk,Insomniac,Tanner,Hunter]