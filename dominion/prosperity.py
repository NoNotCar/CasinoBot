from .base import *
from . import common
from .vanilla import Vanilla
import dib

class Loan(Treasure):
    cost = 3
    desc = "£1\nReveal cards from your deck until you reveal a Treasure. Discard or trash it, discarding the other cards"
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=1
        player.update_hand()
        treasure,to_discard = common.deck_search(player,lambda c:isinstance(c,Treasure))
        if treasure:
            if await game.yn_option(player,True,f"You drew a {treasure.name}! Trash it?"):
                await game.trash(player,treasure)
            else:
                player.discard.add(treasure)
        player.discard.dump(to_discard)

class Watchtower(Action,Reaction):
    cost = 3
    desc = "Draw until you have 6 cards in hand.\nWhen you gain a card with this in hand, you may either trash that card or put it onto your deck."
    hand = "gain"
    async def play(self,game:Dominion,player:DPlayer):
        while len(player.hand)<6:
            if not player.draw(1):
                return
    async def react(self,game:Dominion,player:DPlayer,event:str,**kwargs):
        if card:=kwargs["card"]:
            if card in player.discard:
                choice = await game.choose_option(player,True,["discard","trash","deck"],f"Choose a location for the {card.name} to go: ",True)
                if choice=="deck":
                    player.discard.contents.remove(card)
                    player.deck.add(card)
                elif choice=="trash":
                    player.discard.contents.remove(card)
                    await game.trash(player,card)
class Bishop(Vanilla):
    cost = 4
    money = 1
    vp = 1
    extra_desc = "Trash a card from your hand. +1VP per £2 it costs. Each other player may trash a card from their hand."
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        if trashing:=await common.trash_from_hand(game,player,1,1):
            player.vp+=Cost(trashing[0].get_cost(game,player)).coins//2
            player.update_hand()
        await dib.gather([common.trash_from_hand(game,p,0,1) for p in game.attack_order(player)])

class Monument(Vanilla):
    cost = 4
    money = 2
    vp=1

class Talisman(Treasure,Reaction):
    cost = 4
    desc = "£1\nWhile this is in play: when you buy a non-victory card costing £4 or less, gain a copy of it"
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=1
        if self not in player.reactions["buy"]:
            player.reactions["buy"].append(self)
        player.update_hand()
    async def react(self,game:Dominion,player:DPlayer,event:str,**kwargs):
        card = kwargs["card"]
        if isinstance(card,Card) and not isinstance(card,Victory) and card.get_cost(game,player)<=4:
            await game.gain(player,card.__class__)

class WorkersVillage(Vanilla):
    cost = 4
    actions = 2
    draw = 1
    buys = 1

class City(Vanilla):
    cost = 5
    actions = 2
    draw = 1
    extra_desc = "If there are one or more empty Supply piles, +1 Card. If there are two or more, +1 Buy and +£1."
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        empties = len([0 for s in game.supplies.values() if not s])
        if empties>1:
            player.buys+=1
            player.coins+=1
        if empties>0:
            player.draw(1)

class CountingHouse(Action):
    cost = 5
    desc = "Put all Coppers from your discard pile into your hand"
    async def play(self,game:Dominion,player:DPlayer):
        player.hand.extend(player.discard.draw_all(lambda card:isinstance(card,Copper)))

class Mint(Action):
    cost = 5
    desc = "You may gain a copy of a Treasure card from your hand.\nWhen you buy this, trash all Treasures you have in play."
    async def play(self,game:Dominion,player:DPlayer):
        await game.gain(player,(await game.choose_card(player,[c for c in player.hand if isinstance(c,Treasure)],True,"Choose a Treasure from your hand, or pass.")).__class__)
    async def on_buy(self,game:Dominion,player:DPlayer):
        treasures = []
        for c in player.active[:]:
            if isinstance(c,Treasure):
                treasures.append(c)
                player.active.remove(c)
        await game.trash(player,treasures)

class Mountebank(Action,Attack):
    cost = 5
    desc = "+£2\nEach other player may discard a Curse. If they don't, they gain a Curse and a Copper."
    async def bonus(self,game:Dominion,player:DPlayer):
        player.coins+=2
        player.update_hand()
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        if any(isinstance(c,Curse) for c in target.hand) and await game.yn_option(target,True,"Discard a Curse?"):
            curse = next(c for c in target.hand if isinstance(c,Curse))
            target.hand.remove(curse)
            target.discard.add(curse)
            target.update_hand()

class Vault(Action):
    cost = 5
    desc = "+2 Cards\nDiscard any number of cards for +£1 each.\nEach other player may discard 2 cards, to draw a card."
    async def play(self,game:Dominion,player:DPlayer):
        player.draw(2)
        dumping = await game.choose_cards(player,player.hand,msg="Choose any number of cards to discard.")
        player.coins+=len(dumping)
        player.update_hand()
        await dib.gather([self.others(game,p) for p in game.attack_order(player)])
    async def others(self,game:Dominion,player:DPlayer):
        if len(player.hand)>=2 and await game.yn_option(player,True,"Discard two cards to draw one?"):
            player.discard.dump(await game.choose_cards(player,player.hand,2,2,"Choose cards to discard."))
            player.draw(1)

class Venture(Treasure):
    cost = 5
    desc = "£1\nDraw cards from your deck until you reveal a Treasure. Discard the other cards. Play that Treasure."
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=1
        player.update_hand()
        treasure,to_discard = common.deck_search(player,lambda c:isinstance(c,Treasure))
        if treasure:
            await player.dm(f"You drew a {treasure.name}!")
            await game.play_card(player,treasure)
        player.discard.dump(to_discard)

class Goons(Action,Attack,Reaction):
    cost = 6
    desc = "+1 Buy\n+£2\nEach other player discards down to 3 cards in hand.\nWhile you have this in play, when you buy a card, +1VP."
    async def bonus(self,game:Dominion,player:DPlayer):
        player.buys+=1
        player.coins+=2
        if self not in player.reactions["buy"]:
            player.reactions["buy"].append(self)
        player.update_hand()
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        await common.handsize_attack(game,target,3)
    async def react(self,game:Dominion,player:DPlayer,event:str,**kwargs):
        player.vp+=1
        player.update_hand(True)

class GrandMarket(Vanilla):
    draw = 1
    actions = 1
    money = 2
    buys = 1
    cost = 6
    extra_desc = "You can't buy this if you have any Coppers in play"
    def buyable(self,game:Dominion,player:DPlayer):
        return super().buyable(game,player) and not any(isinstance(c,Copper) for c in player.active)

class Hoard(Treasure,Reaction):
    cost = 6
    desc = "$2\nWhile you have this in play, when you buy a Victory card, gain a Gold."
    async def play(self, game: Dominion, player: DPlayer):
        player.coins += 2
        if self not in player.reactions["buy"]:
            player.reactions["buy"].append(self)
        player.update_hand()

    async def react(self, game: Dominion, player: DPlayer, event: str, **kwargs):
        card = kwargs["card"]
        if isinstance(card, Victory):
            await game.gain(player, Gold)

class Bank(Treasure):
    cost = 7
    desc = "+£1 per Treasure you have in play (including this)"
    auto_order = 1
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=len([a for a in player.active if isinstance(a,Treasure)])
        player.update_hand()
class Expand(Action):
    desc = "Trash a card. If you did, gain a card costing up to £3 more than it"
    cost = 7
    async def play(self,game:Dominion,player:DPlayer):
        await common.remodel(game, player, 3)
class Forge(Action):
    desc = "Trash any number of cards from your hand. Gain a card with cost exactly equal to the total cost in coins of the trashed cards."
    cost = 7
    async def play(self,game:Dominion,player:DPlayer):
        trashing = await game.choose_cards(player,player.hand,msg="Choose any number of cards to trash!")
        if trashing:
            await game.trash(player,trashing)
        total_cost = Cost(sum(t.get_cost(game,player) for t in trashing)).coins
        await common.cost_limited_gain(game,player,total_cost,lambda c:c.get_cost(game,player)==total_cost)
class KingsCourt(Action):
    desc = "Play an Action card from your hand thrice."
    cost = 7
    async def play(self,game:Dominion,player:DPlayer):
        target = await game.choose_card(player, [c for c in player.hand if "ACTION" in c.extype], True,
                                        msg="Choose a card to play thrice.")
        if target:
            await game.play_card(player, target)
            await game.play_card(player, target)
            await game.play_card(player, target)
class Peddler(Vanilla):
    draw = 1
    actions = 1
    money = 1
    cost = 8
    extra_desc = "During a player's Buy phase, this costs £2 less per Action card they have in play."
    def get_cost(self,game:Dominion,player:DPlayer):
        return max(0,8 - (len([a for a in player.active if isinstance(a,Action)])*2 if game.phase=="BUY" else 0))

cards = [Loan,Bishop,Monument,Talisman,WorkersVillage,City,CountingHouse,Mint,Mountebank,Vault,Venture,Goons,GrandMarket,
         Hoard,Bank,Expand,Forge,KingsCourt,Peddler,Watchtower]


