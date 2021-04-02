from .game import *
from .werewolf import Seer, Mason
class Targeted(Role):
    target=None
    message = "Choose someone to target!"
    async def preload(self,game:OneNight):
        await self.user.dm(self.message)
        self.target=await game.dm_tag(self.user,game.other_players(self.user))
class Cockerel(Village,Targeted):
    desc = "You wake up another player, allowing them to view their final role."
    phase = 9
    async def execute(self, game: OneNight, phase:float):
        await self.target.dm(f"You are awoken by a loud crowing, allowing you to find out you are now the {self.target.role.name}")
        game.history.append(f"{self.user.name} woke up {self.target.name}, who found out they were the {self.target.role.name}.")
class Nitwit(Village):
    desc = "Near the start of the night, you swap two random cards"
    phase = 1.1
    singleton = True
    def get_choice(self,game):
        return random.choice(game.players+[1,2,3])
    def stringed(self,choice:typing.Union[int,ONP]):
        return f"center card {choice}" if isinstance(choice,int) else f"{choice.name}'s role"
    async def execute(self, game: OneNight, phase:float):
        p1 = self.get_choice(game)
        while True:
            p2 = self.get_choice(game)
            if p2!=p1:
                break
        game.swap_roles(p1,p2)
        game.history.append(f"{self.user.name} the Nitwit swapped {self.stringed(p1)} with {self.stringed(p2)}.")
class Pacifist(Role):
    team = "pacifist"
    desc = "You win if _nobody_ dies! Break out your best conflict-resolution techniques!"
    def did_win(self,game:OneNight,player:ONP):
        return not any(p.dead for p in game.players)
class Gravedigger(Role):
    team = "gravedigger"
    desc = "As a gravedigger, you _love_ having more work! You win if more than one person dies."
    def did_win(self,game:OneNight,player:ONP):
        return len([p for p in game.players if p.dead])>1
class Soothsayer(Village):
    desc = "You see two other players' roles during the night, but not who they are."
    phase = Seer.phase
    async def execute(self, game: OneNight, phase:float):
        targets = random.sample(game.other_players(self.user),2)
        await self.user.dm(f"You see the {targets[0].role.name} and the {targets[1].role.name}")
        game.history.append(f"{self.user.name} saw the {targets[0].role.name} and the {targets[1].role.name} in a dream.")
    @classmethod
    def set_valid(cls, rset: typing.List[typing.Type[Role]], final:bool):
        if final:
            return len(rset)>3
        return True
class AlphaMale(Role):
    team = "alphas"
    desc = "THERE CAN ONLY BE ONE. You win if you are the _only_ alpha male alive at the end of the night. During the night, you get to see your rival(s)"
    phase = Mason.phase
    async def execute(self, game: OneNight, phase:float):
        other_alphas = [p for p in game.other_players(self.user) if p.role.team=="alphas"]
        if other_alphas:
            await self.user.dm(f"Your rival(s) is {dib.smart_list([o.name for o in other_alphas])}")
            game.history.append(f"{self.user.name}, the ABSOLUTE CHAD they are, woke up and saw {dib.smart_list([o.name for o in other_alphas])}")
        else:
            await self.user.dm("Good news! You're the only alpha! (Well, barring shenanigans later in the night)")
    @classmethod
    def set_valid(cls, rset: typing.List[typing.Type[Role]], final:bool):
        if final:
            return rset.count(AlphaMale)==2
        return False
roles = [Cockerel,Nitwit,Pacifist,Gravedigger,Soothsayer,AlphaMale]
