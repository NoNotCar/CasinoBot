import random
class Policy(object):
    track=None
    name="Policy"
    memo=None
    async def enact(self,game):
        pass
class Liberal(Policy):
    track="liberal"
    name="Liberal"
class Fascist(Policy):
    track="fascist"
    name="Fascist"
class Conservative(Policy):
    track="conservative"
    name="Conservative"
class Shutdown(Policy):
    name="Shutdown"
    memo = "The populace is immediately frustrated."
    async def enact(self,game):
        await game.channel.send("The government shuts down. The populace are frustrated...")
        await game.enact("A frustrated populace", game.policy_deck.pop(), False)
class Terrorism(Policy):
    name="Terrorism"
    memo = "Kills a random player"
    async def enact(self,game):
        victim=random.choice(game.living_players)
        await game.channel.send("%s was killed in a terrorist attack!" % victim.name)
        await game.kill(victim)
class Corruption(Policy):
    name="Corruption"
    memo = "In a special election, the chancellor becomes the next president"
    async def enact(self,game):
        await game.channel.send("In a spectacularly rigged election, %s becomes president!\n(The president order returns to normal afterwards)" % game.chancellor.name)
        game.special_president=game.players.index(game.chancellor)
class Audit(Policy):
    name="Audit"
    memo = "The chancellor looks at the president's party membership"
    async def enact(self,game):
        await game.channel.send("Auditing in progress...")
        await game.chancellor.dm("Target is a member of the %s party" % game.current_president.role.investigate_allegiance)
class Forecast(Policy):
    name="Forecast"
    memo = "The chancellor looks at the top 3 cards of the deck"
    async def enact(self,game):
        await game.chancellor.dm("The next 3 policies are: " + ", ".join(p.name for p in game.policy_deck[-3:]))
class Smear(Policy):
    name="Smear"
    memo = "The president picks a player. They are considered part of the last government next round."
    async def enact(self,game):
        await game.channel.send("President %s, pick a player to smear" % game.current_president.name)
        target=await game.wait_for_tag(game.current_president,game.living_players)
        target.last_government=True

