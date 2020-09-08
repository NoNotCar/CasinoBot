from mud import Role,MUD,MPlayer,Person
import dib
from . import actions, items

class Impostor(Role):
    name="Impostor"
    objective="Kill all the humans! You can consume people to leave no evidence, but this takes time..."
    special_actions = [actions.Consume]
    async def on_become(self,game:MUD,player:MPlayer):
        await super().on_become(game,player)
        fellows=[p for p in game.players if p is not player and isinstance(p.role,Impostor)]
        if fellows:
            await player.dm("Your fellow impostors are: %s" % dib.smart_list([f.mname for f in fellows]))
    def did_win(self,game:MUD,player:MPlayer):
        return not player.dead and all(isinstance(p.role,Impostor) or p.dead for p in game.players)

class Coroner(Role):
    name="Coroner"
    objective = "Investigate a corpse in the morgue"
    special_actions = [actions.Investigate]
    complete=False
    def did_win(self,game:MUD,player:MPlayer):
        return not player.dead and self.complete
class Security(Role):
    name="Security Guard"
    objective = "Kill all the impostors. Your blaster only has one shot, so make it count!"
    async def on_become(self,game:MUD,player:MPlayer):
        await super().on_become(game,player)
        player.items.append(items.Blaster())
        fellows = [p for p in game.players if p is not player and isinstance(p.role, Security)]
        if fellows:
            await player.dm("Your fellow security guards are: %s" % dib.smart_list([f.mname for f in fellows]))
    def did_win(self,game:MUD,player:MPlayer):
        return not player.dead and not any(isinstance(p.role,Impostor) for p in game.players)
class CEO(Role):
    name="CEO"
    objective = "You have left incriminating documents in your office. Destroy them by any means possible."
    singular = True
    def did_win(self,game:MUD,player:MPlayer):
        return not player.dead and not any(isinstance(e,items.Documents) for e in sum(t.items for t in [p for p in game.players]+list(game.all_areas)))

class Activist(Role):
    name="Activist"
    objective = "The CEO has left incriminating documents in their office. Grab them by the end of the game."
    def did_win(self,game:MUD,player:MPlayer):
        return not player.dead and any(isinstance(i,items.Documents) for i in player.items)

class Introvert(Role):
    name="Introvert"
    objective = "End the game alone in a room"
    def did_win(self,game:MUD,player:MPlayer):
        return not player.dead and not any(isinstance(e,Person) and e is not player.person for e in player.area.entities)

class Extrovert(Role):
    name="Extrovert"
    objective = "End the game with another person in the same room"
    def did_win(self,game:MUD,player:MPlayer):
        return not player.dead and any(isinstance(e,Person) and e is not player.person for e in player.area.entities)