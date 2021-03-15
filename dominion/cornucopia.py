from .base import *
from . import common
from .vanilla import Vanilla, Cantrip
import dib

def differently_named(cards:typing.Iterable[Card]):
    return len(set([c.name for c in cards]))
class Hamlet(Cantrip):
    cost = 2
    extra_desc = "You may discard a card for +1 Action.\nYou may discard a card for +1 Buy."
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        if discarding:=await game.choose_card(player,player.hand,True,"Choose a card to discard for +1 Action, or pass."):
            player.discard.add(discarding)
            player.actions+=1
        if discarding:=await game.choose_card(player,player.hand,True,"Choose a card to discard for +1 Buy, or pass."):
            player.discard.add(discarding)
            player.buys+=1
        player.update_hand()

class FortuneTeller(Action,Attack):
    cost = 3
    desc = "+£2\nEach other player reveals cards from the top of their deck until they reveal a Victory card or a Curse. They put it on top and discard the rest."
    async def bonus(self,game:Dominion,player:DPlayer):
        player.coins+=2
        player.update_hand()
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        card,discarding = common.deck_search(target,lambda c: isinstance(c,Curse) or isinstance(c,Victory))
        if card:
            target.deck.add(card)
            await game.send(f"{target.name} topdecked a {card.name}!")
        else:
            await game.send(f"{target.name} doesn't have any Curses or Victory cards in their deck!")
        target.discard.dump(discarding)

class Menagerie(Action):
    cost = 3
    desc = "+1 Action\nIf all the cards in your hand have different names, +3 Cards.\nOtherwise, +1 Card."
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=1
        names = [c.name for c in player.hand]
        if len(names)==len(set(names)):
            player.draw(3)
        else:
            player.draw(1)

class FarmingVillage(Action):
    cost = 4
    desc = "+2 Actions\nReveal cards from your deck until you reveal a Treasure or Action card. Put that card into your hand and discard the rest."
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=2
        card,discarding = common.deck_search(player,lambda c: isinstance(c,Action) or isinstance(c,Treasure))
        if card:
            player.hand.append(card)
        player.discard.dump(discarding)
        player.update_hand()

class Remake(Action):
    cost = 4
    desc = "Do this twice: Trash a card from your hand, then gain a card costing exactly £1 more than it."
    async def play(self,game:Dominion,player:DPlayer):
        await common.remodel(game,player,1,True)
        await common.remodel(game, player, 1, True)

class Harvest(Action):
    cost = 5
    desc = "Reveal the top 4 cards of your deck, then discard them. +£1 per differently named card revealed."
    async def play(self,game:Dominion,player:DPlayer):
        top4 = player.xdraw(4)
        player.coins+=differently_named(top4)
        player.discard.dump(top4)
        player.update_hand()

class HornOfPlenty(Treasure):
    cost = 5
    desc = "Gain a card costing up to £1 per differently named card you have in play (counting this). If it's a Victory card, trash this."
    auto_order = 2
    async def play(self,game:Dominion,player:DPlayer):
        gained = await common.cost_limited_gain(game,player,differently_named(player.active))
        if isinstance(gained,Victory) and self in player.active:
            player.active.remove(self)
            await game.trash(player,self)
class HuntingParty(Cantrip):
    cost = 5
    extra_desc = "Draw cards until you draw one differently named to any in your hand. Put it into your hand and discard the rest."
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        names = {c.name for c in player.hand}
        draw,discard = common.deck_search(player,lambda c:c.name not in names)
        if draw:
            player.hand.append(draw)
            player.update_hand()
        else:
            await player.dm("Sorry, you have no differently named cards to draw!")
        player.discard.dump(discard)
class Jester(Action,Attack):
    cost = 5
    desc = "+£2\nEach other player discards the top card of their deck. If it's a Victory card they gain a Curse; otherwise they gain a copy of the discarded card or you do, your choice."
    async def bonus(self,game:Dominion,player:DPlayer):
        player.coins+=2
        player.update_hand()
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        discarded = target.xdraw(1)
        if discarded:
            card = discarded[0]
            if isinstance(card,Victory):
                game.gain(target,Curse)
            elif card.__class__ not in game.supplies or not game.supplies[card.__class__]:
                await game.send(f"{target.name} discarded a {card.name}, which is not in the Supply.")
            elif await game.yn_option(attacker,True,f"{target.name} discarded a {card.name}. Gain one?"):
                await game.gain(attacker,card.__class__)
            else:
                await game.gain(target,card.__class__)

class Fairgrounds(Victory):
    cost = 6
    desc = "Worth 2VP per 5 differently named cards you have."
    def final_vp(self,game:Dominion,player:DPlayer):
        return (differently_named(player.all_cards)//5)*2

cards = [Hamlet,FortuneTeller,Menagerie,FarmingVillage,Remake,Harvest,HornOfPlenty,HuntingParty,Jester,Fairgrounds]

