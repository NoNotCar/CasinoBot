from . import roles
class Event(object):
    track_emoji=""
    async def do(self,game):
        pass
class Investigate(Event):
    track_emoji = ":mag:"
    async def do(self,game):
        await game.channel.send("INVESTIGATE: The president may now tag someone to find out their party membership")
        target=await game.wait_for_tag(game.current_president,game.living_players)
        await game.current_president.dm("Target is a member of the %s party" % target.role.investigate_allegiance)
class SpecialElection(Event):
    track_emoji = ":crown:"
    async def do(self,game):
        await game.channel.send("SPECIAL ELECTION: The current president picks the next president")
        target = await game.wait_for_tag(game.current_president, [p for p in game.living_players if p is not game.current_president])
        game.special_president=game.players.index(target)
class Peek(Event):
    track_emoji = ":card_box:"
    async def do(self,game):
        await game.channel.send("PEEK: The president looks at the next 3 policies")
        await game.current_president.dm("The next 3 policies are: "+", ".join(p.name for p in game.policy_deck[-3:]))
class Execute(Event):
    track_emoji = ":skull:"
    async def do(self,game):
        await game.channel.send("EXECUTE: The president must choose someone to kill")
        target = await game.wait_for_tag(game.current_president, game.living_players)
        await game.kill(target)
