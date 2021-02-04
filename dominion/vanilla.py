import typing
from .base import *
from . import common
class Cellar(Action):
    cost = 2
    desc = "+1 Action\nDiscard any number of cards, then draw that many."
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=1
        to_discard = await game.choose_cards(player,player.hand,msg="Choose any number of cards to discard!")
        player.discard.dump(to_discard)
        player.draw(len(to_discard))
class Chapel(Action):
    cost = 2
    desc = "Trash up to 4 cards from your hand"
    async def play(self,game:Dominion,player:DPlayer):
        await common.trash_from_hand(game,player,0,4)
class Harbinger(Action):
    cost = 3
    desc = "+1 Card\n+1 Action\nLook through your discard pile. You may put a card from it onto your deck"
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=1
        player.draw(1)
        if player.discard:
            await player.dm("Your discard pile contains: "+player.discard.view())
            if selected:= await game.choose_card(player,player.discard,True,"Choose one to topdeck, or pass."):
                player.deck.add(selected)
        else:
            await player.dm("Your discard pile is empty!")
class Vassal(Action):
    cost = 3
    desc = "+£2\nDiscard the top card of your deck. If it's an Action, you may play it."
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=2
        top = player.xdraw()[0]
        if top:
            if "ACTION" in top.extype:
                if (await game.choose_option(player,True,["yes","no"],f"You drew a {top.name}! Play it?"))=="yes":
                    await game.play_card(player,top)
                    return
            else:
                await player.dm(f"Darn, you drew a {top.name}.")
            player.discard.add(top)
class Vanilla(Action):
    draw = 0
    actions = 0
    buys = 0
    money = 0
    names = ["Card","Action","Buy"]
    extra_desc = ""
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=self.actions
        player.buys+=self.buys
        player.coins+=self.money
        if self.draw:
            player.draw(self.draw)
        else:
            player.update_hand()
    @property
    def desc(self):
        d=""
        for n,q in enumerate([self.draw,self.actions,self.buys]):
            if q:
                if d:
                    d+="\n"
                d+=f"+{q} {self.names[n]+('s' if q>1 else '')}"
        if self.money:
            if d:
                d+="\n"
            d+=f"+£{self.money}"
        if self.extra_desc:
            d+="\n"+self.extra_desc
        return d
class Cantrip(Vanilla):
    draw = 1
    actions = 1
class Village(Vanilla):
    draw = 1
    actions = 2
    cost = 3
class Workshop(Action):
    desc = "Gain a card costing up to £4"
    cost = 3
    max_cost = 4
    async def play(self,game:Dominion,player:DPlayer):
        await common.cost_limited_gain(game,player,self.max_cost)
class Bureaucrat(Action,Attack):
    desc = "Gain a Silver onto your deck.\nEach other player puts a Victory card onto their deck."
    cost = 4
    async def bonus(self,game:Dominion,player:DPlayer):
        game.gain(player,Silver)
    async def attack(self, game: Dominion, target: DPlayer, attacker):
        chosen = await game.choose_card(target,[c for c in target.hand if "VICTORY" in c.extype],msg="Choose a Victory card to topdeck!")
        if chosen:
            target.deck.add(chosen)
            target.update_hand()
class Gardens(Victory):
    cost = 4
    desc = "Worth 1VP per 10 cards you have"
    def final_vp(self, game: Dominion, player: DPlayer):
        return len(player.all_cards)//10
    @classmethod
    def get_supply(cls,players:int):
        return Estate.get_supply(players)
class Militia(Action,Attack):
    desc = "+£2\nEach other player discards down to 3 cards."
    cost = 4
    async def bonus(self,game:Dominion,player:DPlayer):
        player.coins+=2
        player.update_hand()
    async def attack(self, game: Dominion, target: DPlayer, attacker):
        to_discard = max(0,target.hand-3)
        if to_discard:
            chosen = await game.choose_cards(target,target.hand,to_discard,to_discard,f"Choose {to_discard} cards to discard!")
            target.discard.dump(chosen)
class Moneylender(Action):
    desc = "Trash a Copper from your hand. If you did, +£3"
    cost = 4
    async def play(self,game:Dominion,player:DPlayer):
        for c in player.hand:
            if c.name=="Copper":
                await game.trash(player,c)
                player.coins+=1
                player.hand.remove(c)
                player.update_hand()
                break
class Poacher(Vanilla):
    draw = 1
    actions = 1
    money = 1
    cost = 4
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        to_discard = len([s for s in game.supplies.values() if s.empty])
        if to_discard:
            player.discard.dump(await game.choose_cards(player,player.hand,to_discard,to_discard,f"Choose {to_discard} cards to discard!"))
    @property
    def desc(self):
        return super().desc+"\nDiscard a card per empty supply pile"
class Remodel(Action):
    desc = "Trash a card. If you did, gain a card costing up to £2 more than it"
    cost = 4
    async def play(self,game:Dominion,player:DPlayer):
        trashing = await game.choose_card(player,player.hand,msg="Choose a card to trash!")
        if trashing:
            await game.trash(player,trashing)
            await common.cost_limited_gain(game,player,trashing.cost+2)
class Smithy(Vanilla):
    cost = 4
    draw = 3
class ThroneRoom(Action):
    cost = 4
    override_name = "Throne Room"
    desc = "You may play an Action card from your hand twice"
    async def play(self,game:Dominion,player:DPlayer):
        target = await game.choose_card(player,[c for c in player.hand if "ACTION" in c.extype],True,msg="Choose a card to throne.")
        if target:
            await game.play_card(player,target)
            await game.play_card(player,target)
class CouncilRoom(Vanilla):
    draw = 4
    actions = 1
    cost = 5
    override_name = "Council Room"
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        for p in game.players:
            if p is not player:
                p.draw(1)
    @property
    def desc(self):
        return super().desc+"\nEach other player draws a card."
class Festival(Vanilla):
    actions = 2
    buys = 1
    money = 2
    cost = 5
class Lab(Vanilla):
    actions = 1
    draw = 2
    cost = 5
class Market(Vanilla):
    draw = 1
    actions = 1
    buys = 1
    money = 1
    cost = 5
class Mine(Action):
    desc = "You may trash a Treasure from your hand. If you did, gain a Treasure to your hand costing up to £3 more than it"
    cost = 5
    async def play(self,game:Dominion,player:DPlayer):
        trashing = await game.choose_card(player,[c for c in player.hand if "TREASURE" in c.extype],msg="Choose a Treasure to trash!")
        if trashing:
            await game.trash(player,trashing)
            await common.cost_limited_gain(game,player,trashing.cost+3,lambda c:isinstance(c,Treasure),"hand")
class Witch(Action,Attack):
    cost = 5
    desc = "+2 Cards\nEach other player gains a Curse"
    async def bonus(self,game:Dominion,player:DPlayer):
        player.draw(2)
    async def attack(self, game: Dominion, target: DPlayer, attacker):
        game.gain(target,Curse)
class Moat(Action,Defence):
    cost = 2
    desc = "+2 Cards"
    async def play(self,game:Dominion,player:DPlayer):
        player.draw(2)
class Merchant(Vanilla,Reaction):
    cost = 3
    actions = 1
    draw = 1
    bonus = 0
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        player.reactions["play Silver"].append(self)
    async def react(self,game:Dominion,player:DPlayer,event:str):
        player.coins+=1
        return True
    @property
    def desc(self):
        return super().desc+"\nWhen you next play a Silver this turn, +£1"
class Bandit(Action,Attack):
    cost = 5
    desc = "Gain a Gold. Each other player reveals the top 2 cards of their deck, trashes a revealed Treasure other than Copper, and discards the rest."
    async def bonus(self,game:Dominion,player:DPlayer):
        game.gain(player,Gold)
    async def attack(self, game: Dominion, target: DPlayer, attacker):
        drawn = target.xdraw(2)
        trashing = await game.choose_card(target,drawn,False,f"You drew {dib.smart_list([c.name for c in drawn if 'TREASURE' in c.extype and not isinstance(c,Copper)])}. Choose a Treasure to trash.")
        if trashing:
            await game.trash(target,trashing)
        target.discard.dump([d for d in drawn if d!=trashing])
class Library(Action):
    cost = 5
    desc = "Draw until you have 7 cards in hand, skipping any Action cards you choose to, and discarding any skipped cards afterwards"
    async def play(self,game:Dominion,player:DPlayer):
        set_aside = []
        while len(player.hand)<7:
            drawn = player.xdraw(1)
            if drawn:
                card = drawn[0]
                if "ACTION" in card.extype and (await game.choose_option(player,True,["yes","no"],f"You drew a {card.name}! Skip it?",True))=="yes":
                    set_aside.append(card)
                else:
                    player.hand.append(card)
            else:
                break
        player.discard.dump(set_aside)
        player.update_hand()
class Artisan(Action):
    cost = 6
    desc = "Gain a card to your hand costing up to £5.\nPut a card from your hand onto your deck."
    async def play(self,game:Dominion,player:DPlayer):
        await common.cost_limited_gain(game,player,5,destination="hand")
        player.hand.extend(await game.choose_cards(player,player.hand,1,1,"Choose a card to topdeck!"))
cards = [Cellar,Chapel,Harbinger,Vassal,Village,Workshop,Bureaucrat,Gardens,Militia,Moneylender,Poacher,Remodel,Smithy,ThroneRoom,
         Festival,Market,Mine,Lab,CouncilRoom,Witch,Moat,Merchant,Bandit,Library,Artisan]
print(len(cards))
