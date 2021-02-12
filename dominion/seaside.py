from .base import *
from . import common
from .vanilla import Vanilla,Cantrip
import dib

class Haven(Cantrip,Duration):
    cost = 2
    extra_desc = "Set aside a card from your hand. At the start of your next turn, add it to your hand."
    def __init__(self):
        self.set_aside = []
        super().__init__()
    async def first(self,game:Dominion,player:DPlayer):
        self.set_aside.extend(await game.choose_cards(player,player.hand,1,1,"Choose a card to set aside"))
    async def next(self,game:Dominion,player:DPlayer):
        player.hand.extend(self.set_aside)
        self.set_aside.clear()
    async def play(self,game:Dominion,player:DPlayer):
        await Cantrip.play(self,game,player)
        await Duration.play(self,game,player)
class Lighthouse(Action,Duration,Defence):
    cost = 2
    desc = "+1 Action\nNow and at the start of your next turn, +$1.\nWhile you have this in play, when another player plays an Attack card, it doesn't affect you."
    async def first(self,game:Dominion,player:DPlayer):
        player.actions+=1
        player.coins+=1
        player.update_hand()
    async def next(self,game:Dominion,player:DPlayer):
        player.coins+=1
        player.update_hand()
    async def on_block(self,game:Dominion,attacker:DPlayer,targeted:DPlayer):
        return self in targeted.active
class NativeVillage(Vanilla):
    cost = 2
    mat = {}
    actions = 2
    extra_desc = "Choose one: put the top card of your deck onto your Native Village mat, or put all of the cards from the mat into your hand"
    @classmethod
    def setup(cls,game:Dominion):
        cls.mat.clear()
        for p in game.players:
            cls.mat[p]=[]
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        if await game.yn_option(player,True,"Put the top card of your deck onto the mat?"):
            if cards:=player.xdraw(1):
                self.mat[player].extend(cards)
                await player.dm(f"Your mat now contains {dib.smart_list([c.name for c in self.mat[player]])}.")
            else:
                await player.dm("You don't have any cards in your deck or discard :cry:")
        else:
            player.hand.extend(self.mat[player])
            self.mat[player].clear()
    @classmethod
    def teardown(cls,game:Dominion):
        for p,cards in cls.mat:
            p.deck.dump(cards)

class PearlDiver(Cantrip):
    cost = 2
    extra_desc = "Look at the bottom card of your deck. You may put it on top"
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        if not player.deck:
            player.deck.dump(player.xdraw(1))
        if len(player.deck):
            bottom = player.deck.bottom
            if await game.yn_option(player,True,f"Your bottom card is {bottom.name}. Put it on top?"):
                player.deck.contents.remove(bottom)
                player.deck.add(bottom)
        else:
            await player.dm("Your deck and discard pile are empty!")
class Ambassador(Action,Attack):
    revealed = None
    cost = 3
    desc = "Reveal a card from your hand. Return up to 2 copies of it from your hand to the Supply. Each other player gains a copy of it."
    async def bonus(self,game:Dominion,player:DPlayer):
        self.revealed=None
        if revealed:=await game.choose_card(player,player.hand[:],False,"Choose a card to reveal!"):
            self.revealed=revealed.__class__
            if self.revealed in game.supplies:
                matching = [c for c in player.hand if isinstance(c,self.revealed)]
                num=await game.choose_number(player,True,0,len(matching),"How many would you like to return?")
                actually_returning = matching[:num]
                for a in actually_returning:
                    player.hand.remove(a)
                game.supplies[self.revealed].dump(actually_returning)
            else:
                self.revealed=None
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        if self.revealed:
            await game.gain(target,self.revealed)
class CutPurse(Action,Attack):
    cost = 4
    desc = "+£2\nEach other player discards a Copper."
    async def bonus(self,game:Dominion,player:DPlayer):
        player.coins+=2
        player.update_hand()
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        if coppers:=[c for c in target.hand if isinstance(c,Copper)]:
            target.hand.remove(coppers[0])
            target.discard.add(coppers[0])

class Lookout(Vanilla):
    cost = 3
    actions = 1
    extra_desc = "Look at the top 3 cards of your deck. Trash one of them. Discard one of them. Put the other one back on top of your deck."
    async def play(self, game: Dominion, player: DPlayer):
        await super().play(game, player)
        top3 = player.xdraw(3)
        print(top3)
        if top3:
            await player.dm(f"You top 3 cards are: {dib.smart_list([c.name for c in top3])}")
            trashing = await game.choose_card(player,top3,False,"Choose a card to trash!")
            await game.trash(player,trashing)
            if top3:
                discarding = await game.choose_card(player, top3, False, "Choose a card to discard!")
                player.discard.add(discarding)
                player.deck.dump(top3)

class FishingVillage(Action,Duration):
    cost = 3
    desc = "+2 Actions\n+£1\nAt the start of your next turn: +1 Action and +£1."
    async def first(self,game:Dominion,player:DPlayer):
        player.actions+=2
        player.coins+=1
        player.update_hand()
    async def next(self,game:Dominion,player:DPlayer):
        player.actions += 1
        player.coins += 1
        player.update_hand()
class Warehouse(Vanilla):
    cost = 3
    draw = 3
    actions = 1
    extra_desc = "Discard 3 cards"
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        player.discard.dump(await game.choose_cards(player,player.hand,3,3,"Choose 3 cards to discard!"))
class Caravan(Cantrip,Duration):
    cost = 4
    extra_desc = "At the start of your next turn, +1 Card"
    async def next(self,game:Dominion,player:DPlayer):
        player.draw(1)
    async def play(self,game:Dominion,player:DPlayer):
        await Cantrip.play(self,game,player)
        await Duration.play(self,game,player)
class Salvager(Action):
    cost = 4
    desc = "+1 Buy\nTrash a card from your hand. +£1 per £1 it costs"
    async def play(self,game:Dominion,player:DPlayer):
        player.buys+=1
        if trashed:=await common.trash_from_hand(game,player,1,1):
            player.coins+=int(trashed[0].get_cost(game,player))
        player.update_hand()
class SeaHag(Action,Attack):
    cost = 4
    desc = "Each other player discards the top card of their deck, then gains a Curse onto their deck."
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        target.discard.dump(target.xdraw(1))
        await game.gain(target,Curse,"deck")
class TreasureMap(Action):
    cost = 4
    desc = "Trash this and another Treasure Map from your hand. If you did, gain 4 Golds to the top of your deck."
    async def play(self,game:Dominion,player:DPlayer):
        success = True
        if self in player.active:
            player.active.remove(self)
            await game.trash(player,self)
        else:
            success=False
        if any(isinstance(c,TreasureMap) for c in player.hand):
            target = next(c for c in player.hand if isinstance(c,TreasureMap))
            player.hand.remove(target)
            await game.trash(player,self)
            player.update_hand()
        else:
            success=False
        if success:
            await player.dm("HOORAY! YOU FOUND THE TREASURE!")
            for _ in range(4):
                await game.gain(player,Gold,"deck")
class Bazaar(Vanilla):
    cost = 5
    money = 1
    actions = 2
    draw = 1
class Explorer(Action):
    cost = 5
    desc = "If you have a Province in hand, gain a Gold to your hand. Otherwise, gain a Silver to your hand"
    async def play(self,game:Dominion,player:DPlayer):
        if any(isinstance(c,Province) for c in player.hand):
            await game.gain(player,Gold,"hand")
        else:
            await game.gain(player,Silver,"hand")
class MerchantShip(Action,Duration):
    cost = 5
    desc = "Now and at the start of your next turn, +£2"
    async def first(self,game:Dominion,player:DPlayer):
        player.coins+=2
        player.update_hand()
    async def next(self,game:Dominion,player:DPlayer):
        await self.first(game,player)
class Tactician(Action,Duration):
    cost = 5
    desc = "If you have at least one card in hand, discard your hand, and at the start of your next turn, +5 Cards, +1 Action, and +1 Buy."
    triggered = 0
    async def first(self,game:Dominion,player:DPlayer):
        if player.hand:
            self.triggered+=1
            player.discard.dump(player.hand)
    async def next(self,game:Dominion,player:DPlayer):
        if self.triggered>0:
            self.triggered-=1
            player.actions+=1
            player.buys+=1
            player.draw(5)
class Wharf(Action,Duration):
    cost = 5
    desc = "Now and at the start of your next turn: +2 Cards and +1 Buy."
    async def first(self,game:Dominion,player:DPlayer):
        player.buys+=1
        player.draw(2)
    async def next(self,game:Dominion,player:DPlayer):
        await self.first(game,player)

cards = [Haven, Lighthouse, NativeVillage,PearlDiver,Lookout,FishingVillage,Warehouse,Caravan,Salvager,SeaHag,
         TreasureMap,Bazaar,Explorer,MerchantShip,Wharf,Tactician,Ambassador]

