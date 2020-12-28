from asyncio import create_task as task
import random
class Evil(object):
    evil=True
    vote_options=["approve","reject"]
    mission_options=["success", "fail"]
    true_name="Neutral Evil"
    emoji=":smiling_imp:"
    help="Fail some missions or something"
    game=None
    singular=False
    def __init__(self,player):
        self.player=player
    async def on_become(self):
        await self.player.dm("You are %s!" % self.name)
        await self.player.dm(self.help)
    async def on_game_start(self,game):
        self.game=game
        if self.evil:
            await self.player.dm("Your fellow evildoers are: "+" ".join(p.name for p in game.players if p.role.known_to_evil and p is not self.player))
    async def on_round_start(self,game):
        pass
    async def can_vote(self,vote):
        if vote in self.vote_options:
            return vote
        await task(self.player.dm("That's not a valid vote option!"))
        return False
    async def can_action(self,action):
        if action in self.mission_options:
            return action
        await task(self.player.dm("That's not a valid mission option!"))
        return False
    def did_win(self,game,evil_wins):
        return self.evil==evil_wins
    @classmethod
    def random_valid(cls,other_roles):
        return not (cls.singular and cls in other_roles)
    @property
    def name(self):
        return self.true_name+" "+self.emoji
    @property
    def appears_evil(self):
        return self.evil
    @property
    def known_to_evil(self):
        return self.evil
    @property
    def lady_evil(self):
        return self.evil
class NeutGood(Evil):
    evil = False
    mission_options = ["success"]
    true_name="Neutral Good"
    emoji=":slight_smile:"
    help="Use your big brain energy to logic out the evildoers!"
class Merlin(NeutGood):
    true_name="Merlin"
    emoji=":man_mage:"
    help = "You know evil, but don't get caught!"
    singular = True
    async def on_game_start(self,game):
        await self.player.dm("The evildoers are: "+" ".join(p.name for p in game.players if p.role.appears_evil))
class Morgana(Evil):
    true_name = "Morgana"
    emoji=":woman_detective:"
    help = "You appear as Merlin. Mislead Percival as much as possible!"
    singular = True
    @classmethod
    def random_valid(cls,other_roles):
        return Percival in other_roles and cls not in other_roles
class Reverser(Evil):
    mission_options = ["success","reverse"]
    true_name="Evil Reverser"
    emoji=":shrug:"
    help = "You're evil, but can only fail missions by reversing them..."
    @classmethod
    def random_valid(cls,other_roles):
        return GoodReverser in other_roles or Reverser in other_roles
class GoodReverser(Reverser):
    evil = False
    true_name = "Good Reverser"
    emoji=":man_shrugging:"
    help = "You can reverse the outcome of missions! Use this power wisely..."
    @classmethod
    def random_valid(cls,other_roles):
        return True
class Arthur(NeutGood):
    vote_options = ["approve","reject","veto"]
    true_name = "Arthur"
    emoji=":crown:"
    help = "If evil wins two missions, you gain the ability to veto missions at the cost of losing voting information"
    singular=True
    async def can_vote(self,vote):
        if vote=="veto":
            if self.game.results.count(0)!=2:
                await task(self.player.dm("You can't veto yet..."))
                return False
            else:
                return "veto"
        return await super().can_vote(vote)
class Percival(NeutGood):
    true_name = "Percival"
    emoji=":cop:"
    help = "You know who Merlin and Morgana are, but not which is which..."
    known = [Merlin,Morgana]
    async def on_game_start(self,game):
        await self.player.dm("You have detected: " + " ".join(p.name for p in game.players if p.role.__class__ in self.known))
    @classmethod
    def random_valid(cls,other_roles):
        return Percival not in other_roles and all(k in other_roles for k in cls.known)
class Oberon(Evil):
    true_name="Oberon"
    emoji=":clown:"
    help = "You're evil, but didn't quite manage to make it to the evildoers meeting. Pretend you're good until the time is right!"
    known_to_evil=False
    singular = True
    async def on_game_start(self,game):
        pass
class Mordred(Evil):
    true_name="Mordred"
    emoji=":japanese_ogre:"
    help = "Your dark magics cloak you from Merlin. This is probably useful."
    appears_evil=False
    singular = True
class Mordrod(Evil):
    evil = False
    true_name = "Mordrod"
    emoji = ":woozy_face:"
    help="You've suffered a concussion and think you're Mordred. You actually know random people, can't actually fail missions and win with the good team."
    async def on_become(self):
        fake_mordred=Mordred(self.player)
        await fake_mordred.on_become()
    async def on_game_start(self,game):
        evils=len([p for p in game.players if p.role.known_to_evil])-1
        allowed = [p for p in game.players if p is not self.player]
        await self.player.dm("Your fellow evildoers are: " + " ".join(p.name for p in random.sample(allowed, evils)))
    async def can_action(self,action):
        if await super().can_action(action):
            return "success"
    @classmethod
    def random_valid(cls,other_roles):
        return cls not in other_roles and Mordred in other_roles
class Phantom(Evil):
    true_name = "Phantom"
    emoji = ":ghost:"
    help = "You're evil, but your ability to affect the material world is... unreliable"
    mission_options = ["random"]
    singular = True
    async def can_action(self,action):
        if await super().can_action(action):
            return random.choice(Evil.mission_options)
        return False
class Tanner(NeutGood):
    true_name = "Tanner"
    emoji = ":poop:"
    help = "You only win if good won _and_ you were assassinated. You have no additional info. Good luck..."
    singular = True
    def did_win(self,game,evil_wins):
        return not evil_wins and self.player is game.murdered
class Plagued(NeutGood):
    mission_options = ["fail"]
    true_name = "Plagued"
    emoji = ":sick:"
    help = "You're good but are too ill to succeed missions..."
    @classmethod
    def random_valid(cls,other_roles):
        return cls not in other_roles and GoodReverser in other_roles
class Merlon(NeutGood):
    true_name = "Merlon"
    emoji = ":mage:"
    help = "Thinks they're Merlin, but they actually only know random people :P"
    async def on_become(self):
        fake_merlin=Merlin(self.player)
        await fake_merlin.on_become()
    async def on_game_start(self, game):
        evils=len([p.name for p in game.players if p.role.appears_evil])
        allowed=[p for p in game.players if p is not self.player]
        await self.player.dm("The evildoers are: " + " ".join(p.name for p in random.sample(allowed,evils)))
    @classmethod
    def random_valid(cls,other_roles):
        return cls not in other_roles and Merlin in other_roles
class Loncelot(Evil):
    true_name = "Loncelot"
    emoji = ":man_supervillain:"
    help = "You start evil, but from round 3 your allegiance may switch!"
    def __init__(self,player):
        super().__init__(player)
        self.random=random.Random()
    async def on_game_start(self,game):
        self.random.setstate(game.seed)
    async def on_round_start(self,game):
        if game.cround>=3:
            if self.random.randint(0,1):
                self.evil=not self.evil
                await self.player.dm("Your allegiance has switched to %s!" % ("evil" if self.evil else "good"))
    @property
    def mission_options(self):
        return ["success","fail"] if self.evil else ["success"]
    @classmethod
    def random_valid(cls,other_roles):
        return cls not in other_roles and Lancelot in other_roles
class Lancelot(Loncelot):
    true_name = "Lancelot"
    emoji = ":man_superhero:"
    help = "You start good, but from round 3 your allegiance may switch!"
    evil = False
    @classmethod
    def random_valid(cls, other_roles):
        return cls not in other_roles and Loncelot in other_roles
class Dodgy_Dave(NeutGood):
    true_name = "Dodgy Dave"
    emoji = ":smirk:"
    help = "You're good, but have committed enough minor crimes that everyone except the lady (and yourself) thinks you're evil."
    appears_evil=True
    known_to_evil=True
    singular = True
class Boris(Evil):
    evil = False
    true_name = "Boris"
    emoji = ":blond_haired_man:"
    help = "You're good but you only want the good team to win in round 5 so you can privatise the NHS in the chaos. You're not above playing fail cards to achieve this..."
    singular = True
    def did_win(self,game,evil_wins):
        return game.cround==5 and not evil_wins
class Corbyn(NeutGood):
    evil = True
    known_to_evil=False
    appears_evil=False
    lady_evil=False
    true_name = "Corbyn"
    emoji = ":man_white_haired:"
    help="You know Boris and win only if he is not on the final mission. You can only succeed missions."
    async def on_game_start(self,game):
        for p in game.players:
            if isinstance(p.role,Boris):
                await self.player.dm("The leader of the opposition is %s!" % p.name)
    @classmethod
    def random_valid(cls,other_roles):
        return cls not in other_roles and Boris in other_roles
    def did_win(self,game,evil_wins):
        return any(isinstance(p.role,Boris) for p in game.past_missions[-1][0])
class Mason(NeutGood):
    true_name = "Mason"
    emoji = ":construction_worker:"
    help = "You're good and know who the other Mason is. Beware, if you reveal this the evil team is going to have an easier time finding Merlin!"
    async def on_game_start(self,game):
        await self.player.dm("Your fellow Mason is: " + [p.name for p in game.players if isinstance(p.role,Mason) and p is not self.player][0])
    @classmethod
    def random_valid(cls,other_roles):
        return other_roles.count(Mason)==1
class Terrorist(Evil):
    true_name = "Terrorist"
    emoji = ":radioactive:"
    mission_options = ["bomb"]
    help = "You must try and get on a mission in order to detonate your bomb, in which case only you win. Unfortunately Percival (and the lady) know who you are..."
    appears_evil = False
    known_to_evil = False
    async def on_game_start(self,game):
        for p in game.players:
            if isinstance(p.role,Percival):
                await p.dm("You have found evidence to suggest %s is the terrorist!" % self.player.name)
    @classmethod
    def random_valid(cls,other_roles):
        return False
        #return cls not in other_roles and Percival in other_roles
class Lady(NeutGood):
    true_name = "Lady"
    emoji = ":dancer:"
    help="You are good, and are always informed of the true result of any ladying."
    singular = True
class Sheep(NeutGood):
    true_name = "Sheep"
    emoji = ":sheep:"
    help="You're good, but your vote is copied from a random player"
    vote_options = ["sheep"]
class Goat(Evil):
    true_name = "Goat"
    emoji = ":goat:"
    help = "You're evil, but your vote is copied from a random player"
    vote_options = ["sheep"]
all_roles=[Evil,NeutGood,Merlin,Merlon,Morgana,Mordred,Mordrod,Percival,Arthur,GoodReverser,Reverser,Oberon,Phantom,Tanner,Plagued,Lancelot,Loncelot,Dodgy_Dave,Boris,Mason,Terrorist,Corbyn,Lady,Sheep,Goat]
rdict={r.true_name:r for r in all_roles}
presets={"random":[],"lancelot":[Lancelot,Loncelot],"plague":[Plagued,GoodReverser,Reverser],"reversal":[GoodReverser,Reverser],
         "confusion": [Merlon,Mordred,Mordrod],"politics":[Corbyn,Boris],"farmer":[Sheep,Goat]}