from .base import *
from .vanilla import Vanilla
from . import common

class EpicFail(Defeat):
    desc = "-3VP\nWhen you trash this, gain a Curse"
    total = 999
    def final_vp(self, game: Dominion, player: DPlayer):
        return -3
    async def on_trash(self, game: Dominion, player: DPlayer):
        await game.gain(player,Curse)
class PyramidScheme(Action,Attack):
    cost = 3
    desc = "Each opponent must either give you a Copper from their hand, or gain a Copper to their hand if they have no Copper"
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        try:
            copper = next(c for c in target.hand if isinstance(c,Copper))
            target.hand.remove(copper)
            attacker.hand.append(copper)
        except StopIteration:
            await game.gain(target,Copper,"hand")

class TrueZen(Action):
    desc = "+£5\nTrash your hand"
    override_name = "True Zen"
    cost = 4
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=5
        await game.trash(player,player.hand)
        player.hand.clear()
        player.update_hand()

class VillageIdiot(Action):
    desc = "+1 Card\n+4 Actions\n-1 Action per Action in your hand."
    cost = 2
    override_name = "Village Idiot"
    async def play(self,game:Dominion,player:DPlayer):
        player.draw(1)
        player.actions+=4
        player.actions-=len([c for c in player.hand if "Action" in c.extype])
        player.update_hand()
class QueensCourt(Action):
    cost = 7
    desc = "You may play any number of Action cards from your hand twice"
    async def play(self,game:Dominion,player:DPlayer):
        targets = await game.choose_cards(player,[c for c in player.hand if "ACTION" in c.extype],msg="Choose a card to throne.")
        for target in targets:
            await game.play_card(player,target)
            await game.play_card(player,target)
class RHM(Action):
    cost = 4
    override_name = "Right-hand Man"
    desc = "+2 Coffers. Put this on top of your deck."
    async def play(self,game:Dominion,player:DPlayer):
        player.coffers+=2
        if self in player.active:
            player.active.remove(self)
            player.deck.add(self)
        player.update_hand()
class WildHorse(Vanilla):
    cost = 2
    draw = 2
    actions = 1
    extra_desc = "Look at the top card of your deck. If it's a Treasure, the next player gains this to their hand. If it's an Action, the previous player gains this to their hand."
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        if look:=player.xdraw(1):
            look=look[0]
            await player.dm(f"The top card of your deck is: {look}")
            if self in player.active:
                p_order = list(game.attack_order(player))
                target = p_order[0] if isinstance(look,Treasure) else p_order[-1] if isinstance(look,Action) else None
                if target:
                    player.active.remove(self)
                    target.hand.append(self)
                    target.update_hand()
                    await game.send(f"{player.name}'s Wild Horse ran to {target.name}'s hand!")
class Intern(Action):
    cost = 2
    desc = "If you have no Actions remaining, +2 Cards\nOtherwise, +1 Card, +2 Actions"
    async def play(self,game:Dominion,player:DPlayer):
        if not player.actions:
            player.draw(2)
        else:
            player.actions+=2
            player.draw(1)
class JackOfNoTrades(Action):
    desc = "Gain a Copper.\nReveal the top card of your deck.\nDraw until you have 4 or more cards in hand.\nYou may trash an Action card from your hand."
    async def play(self,game:Dominion,player:DPlayer):
        await game.gain(player,Copper)
        if look:=player.xdraw(1):
            look=look[0]
            await player.dm(f"You have a {look.name} on top of your deck!")
            await game.send(f"{player.name} has a {look.name} on top of their deck!")
        while len(player.hand)<4:
            player.draw(1)
        await common.trash_from_hand(game,player,0,1)
class Nitroglycerin(Action):
    cost = 1
    desc = "When you play or trash this, +1 Action and trash the top 2 cards of your deck"
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=1
        player.update_hand()
        top2 = player.xdraw(2)
        if top2:
            await player.dm(f"You trashed: {dib.smart_list([t.name for t in top2])}!")
            await game.trash(player,top2)
    async def on_trash(self,game:Dominion,player:DPlayer):
        await self.play(game,player)
class Commandeer(Action,common.Command):
    cost = 3
    desc = "Choose an opponent. Choose an non-Command Action card from their hand and play it, leaving it there."
    async def play(self,game:Dominion,player:DPlayer):
        opponent = await game.dm_tag(player,list(game.attack_order(player)))
        valid = [c for c in opponent.hand if isinstance(c,Action) and not isinstance(c,common.Command)]
        if action:=await game.choose_card(player,valid,msg=f"Choose an action to play. Options: {dib.smart_list([v.name for v in valid])}"):
            await action.play(game,player)
class AirConditioning(Action):
    cost = 4
    desc = "Draw until you have 5 cards in hand.\nIf you have no Actions, +2 Actions\nIf you have less than 2 Buys, +1 Buy"
    async def play(self,game:Dominion,player:DPlayer):
        while len(player.hand)<5:
            player.draw(1)
        if player.actions<=0:
            player.actions+=2
        if player.buys<2:
            player.buys+=1
class DemolitionCrew(Action):
    cost = 2
    desc = "Trash all your exiled cards.\nExile the top 3 cards of your deck."
    async def play(self,game:Dominion,player:DPlayer):
        await game.trash(player,player.exiled)
        top3 = player.xdraw(3)
        if top3:
            await player.dm(f"Exiled {dib.smart_list([t.name for t in top3])}!")
            await game.exile(player,top3)
cards = [PyramidScheme,TrueZen,VillageIdiot,QueensCourt,RHM,WildHorse,Intern,JackOfNoTrades,Nitroglycerin,Commandeer,AirConditioning,
         DemolitionCrew]