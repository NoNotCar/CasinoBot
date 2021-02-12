from .base import *
from . import common
from .vanilla import Vanilla,Cantrip

class Ransom(SimpleTreasure,Reaction):
    cost = 5
    income = 2
    hand = "trash"
    desc = "£2\nWhen one of your cards is trashed, you may discard this from your hand to gain a card costing up to £2 more than the trashed card"
    async def react(self,game:Dominion,player:DPlayer,event:str,**kwargs):
        card = kwargs.get("card",None)
        if card and await game.yn_option(player,True,"Discard Ransom?"):
            player.hand.remove(self)
            player.discard.add(self)
            await common.cost_limited_gain(game,player,card.cost+2)

class Backstreet(Night):
    cost = 5
    desc = "+1 Coffer per Action you have.\n+1 Villager per coin you have."
    async def play(self,game:Dominion,player:DPlayer):
        player.coffers+=player.actions
        player.villagers+=player.coins
        player.update_hand()

class SecludedVillage(Action,Victory):
    cost = 5
    desc = "+2 Villagers\nWorth 1VP per 2 Villagers you have."
    async def play(self,game:Dominion,player:DPlayer):
        player.villagers+=2
        player.update_hand()
    def final_vp(self,game:Dominion,player:DPlayer):
        return player.villagers//2

class CursedTome(Action,Attack):
    cost = 5
    desc = "Draw up to 7 cards. If you have 4 or more different card types in your hand, each other player gains a Curse"
    async def play(self,game:Dominion,player:DPlayer):
        while len(player.hand)<7:
            player.draw(1)
        types = set()
        for c in player.hand:
            types.union(c.extype)
        if len(types)>=4:
            await game.send(f"{player.name} has 4 or more card types, cursing everyone!")
            await super().play(game,player)
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        await game.gain(target,Curse)

class Redevelop(Action):
    cost = 6
    desc = "+1 Action\nTrash a card from your hand. If you did, gain a card costing up to £2 more.\nPut this onto your deck"
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=1
        trashing = await common.trash_from_hand(game,player,1,1)
        if trashing:
            await common.cost_limited_gain(game,player,trashing[0].cost+2)
        if self in player.active:
            player.active.remove(self)
            player.deck.add(self)

class Architect(Action):
    cost = 4
    desc = "+2 Cards\nGain a card costing up to £4\nYou may trash this and 2 Silvers from your hand. If you did, gain a Redevelop"
    async def play(self,game:Dominion,player:DPlayer):
        player.draw(2)
        await common.cost_limited_gain(game,player,4)
        silvers = [p for p in player.hand if isinstance(p,Silver)]
        if self in player.active and len(silvers)>=2 and await game.yn_option(player,True,"Trash this and 2 Silvers?"):
            silvers=silvers[:2]
            player.active.remove(self)
            for s in silvers:
                player.hand.remove(s)
            await game.trash(player,[self]+silvers)
            await game.gain(player,Redevelop)
            player.update_hand()
    @classmethod
    def setup(cls,game:Dominion):
        game.add_nonsupply_pile(Redevelop)

class Potlatch(Action):
    cost = 5
    desc = "Gain a card costing up to £6. Each player (including you) gains a card costing less than it."
    async def play(self,game:Dominion,player:DPlayer):
        gained = await common.cost_limited_gain(game,player,6)
        if gained:
            await dib.gather([common.cost_limited_gain(game,p,gained.cost-1) for p in game.players])

class Farmer(Action):
    cost = 5
    desc = "Take the top 6 cards of your deck, put one of each differently named card into your hand and discard the rest."
    async def play(self,game:Dominion,player:DPlayer):
        top6 = player.xdraw(6)
        valid = []
        invalid = []
        for c in top6:
            if not any(oc.name==c.name for oc in valid):
                valid.append(c)
            else:
                invalid.append(c)
        player.draw_cards(valid)
        player.discard.dump(invalid)

class Alderman(Action):
    cost = 6
    desc = "You may play an Action card from your hand twice. If you did, you may spend a Villager to play it again.\nWhen you gain this, +3 Villagers"
    async def play(self,game:Dominion,player:DPlayer):
        target = await game.choose_card(player, [c for c in player.hand if "ACTION" in c.extype], True,msg="Choose a card to play twice.")
        if target:
            await game.play_card(player, target)
            await game.play_card(player, target)
            if player.villagers and await game.yn_option(player,True,"Spend a villager?"):
                player.villagers-=1
                player.update_hand()
                await game.play_card(player,target)
    async def on_gain(self,game:Dominion,player:DPlayer):
        player.villagers+=3
        player.update_hand()
class SilverWorker(Action):
    desc = "+3 Cards\nDiscard a card per Silver in you hand.\nWhen you gain this, each other player gains a Silver onto their deck."
    cost = 3
    async def play(self,game:Dominion,player:DPlayer):
        player.draw(3)
        silvers = len([c for c in player.hand if isinstance(c,Silver)])
        player.discard.dump(await game.choose_cards(player,player.hand,silvers,silvers,f"Choose {silvers} cards to discard!"))
    async def on_gain(self,game:Dominion,player:DPlayer):
        for p in game.attack_order(player):
            await game.gain(player,Silver,"deck")
class Actor(Vanilla):
    villagers = 1
    draw = 1
    cost = 1
class MotherlyWitch(Action,Attack,Duration):
    cost = 5
    desc = "Each other player gains a Curse.\nNow and at the start of your next turn, +2 Cards.\nWhile this is in play, gain a Copper when another player plays an Attack card."
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        await game.gain(target,Curse)
    async def first(self,game:Dominion,player:DPlayer):
        player.draw(2)
    async def next(self,game:Dominion,player:DPlayer):
        player.draw(2)
    async def play(self,game:Dominion,player:DPlayer):
        await Attack.play(self,game,player)
        await Duration.play(self,game,player)
        player.reactions["attacked"].append(self)
    async def react(self,game:Dominion,player:DPlayer,event:str,**kwargs):
        if event=="attacked":
            await game.gain(player,Copper)
        else:
            await Duration.react(self,game,player,event,**kwargs)
class Midwife(Action,Night):
    cost = 3
    desc = "If it's your Night phase, +1 Villager.\nOtherwise, +2 Actions, +£1"
    async def play(self,game:Dominion,player:DPlayer):
        if game.phase=="NIGHT":
            player.villagers+=1
        else:
            player.actions+=2
            player.coins+=1
        player.update_hand()
class HillsideCity(Vanilla):
    cost = 5
    extra_desc = "If you have an even number of cards in your hand, +1 Card"
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        if not len(player.hand)%2:
            player.draw(1)
class KingsCounsel(Action):
    cost = 3
    desc = "The player to your left chooses an Action card from your hand. Play it thrice."
    async def play(self,game:Dominion,player:DPlayer):
        chooser = next(game.attack_order(player))
        target = await game.choose_card(chooser, [c for c in player.hand if "ACTION" in c.extype], True,
                                        msg=f"Choose a card for {player.name} to play thrice. Their hand: {', '.join(c.name for c in player.hand)}")
        if target:
            await game.play_card(player, target)
            await game.play_card(player, target)
            await game.play_card(player, target)
cards = [Ransom,Backstreet,SecludedVillage,CursedTome,Architect,Farmer,Alderman,SilverWorker,Actor,MotherlyWitch,Midwife,
         HillsideCity,KingsCounsel]
