import asyncio
task = asyncio.create_task
class Liberal(object):
    allegiance="liberal"
    vote_options=["ja","nein"]
    true_name="Liberal"
    emoji=":bird:"
    help="Prevent the rise of fascism!"
    game=None
    singular=False
    def __init__(self,player):
        self.player=player
    async def on_become(self):
        await self.player.dm("You are %s!" % self.name if self.singular else "You are a %s!" % self.name)
        await self.player.dm(self.help)
    async def on_game_start(self,game):
        self.game=game
    async def on_round_start(self,game):
        pass
    async def on_death(self,game):
        pass
    async def can_vote(self,vote):
        if vote in self.vote_options:
            return vote
        await task(self.player.dm("That's not a valid vote option!"))
        return False
    def did_win(self,game,winning_team):
        return self.allegiance==winning_team
    @classmethod
    def random_valid(cls,other_roles):
        return not (cls.singular and cls in other_roles)
    @property
    def name(self):
        return self.true_name+" "+self.emoji
    @property
    def known_to_fascists(self):
        return self.allegiance=="fascist"
    @property
    def investigate_allegiance(self):
        return self.allegiance
class Sheep(Liberal):
    true_name = "Sheep"
    emoji = ":sheep:"
    help = "Baa!"
    vote_options = ["sheep"]
class Fascist(Liberal):
    allegiance = "fascist"
    true_name = "Fascist"
    emoji = ":rage:"
    help = "Pass fascist policies and get Hitler into power!"
    async def on_game_start(self,game):
        fascists=[p for p in game.players if p is not self.player and p.role.known_to_fascists]
        hitler=[p for p in game.players if isinstance(p.role,Hitler)][0]
        if fascists:
            await self.player.dm("Your fellow fascists are: "+", ".join(p.name for p in fascists))
        if hitler is not self.player:
            await self.player.dm("%s is Hitler." % hitler.name)
class Goat(Fascist):
    true_name = "Goat"
    emoji = ":goat:"
    help = "Flail around and cause massive property damage!"
    vote_options = ["sheep"]
class Hitler(Fascist):
    true_name = "Hitler"
    emoji = ":face_with_symbols_over_mouth:"
    help="Get elected as Chancellor!"
    singular = True
    async def on_game_start(self,game):
        if len(game.players)<7:
            await super().on_game_start(game)
    async def on_death(self,game):
        await game.channel.send("HITLER has been SHOT!")
        await game.win("liberal")
    @property
    def known_to_fascists(self):
        return False
class Conservative(Liberal):
    true_name = "Conservative"
    emoji = ":face_with_monocle:"
    help = "Pass 3 conservative policies!"
    allegiance = "conservative"
class Tanner(Liberal):
    true_name = "Tanner"
    emoji = ":poop:"
    help = "Get yourself killed! Appears as fascist in investigations"
    allegiance = "tanner"
    async def on_death(self,game):
        await game.channel.send("The Tanner has been killed! You no longer have any leather and society collapses.")
        await game.win("tanner")
    @property
    def investigate_allegiance(self):
        return "fascist"
