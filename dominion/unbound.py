from .base import *
from . import common
from .vanilla import Vanilla,Cantrip,Lab
from .unhinged import EpicFail
import random

class RogueScientist(Action):
    desc = "+5 Debt\nClone a Lab."
    cost = 3
    async def play(self,game:Dominion,player:DPlayer):
        await game.gain(player,Lab,cloned=True)
        player.debt+=5
        player.update_hand()

class GreyGoo(Action):
    desc = "+1 Action\nDuplicate a random non-Victory card in your hand."
    cost = 5
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=1
        if valid:= [c for c in player.hand if not isinstance(c,Victory)]:
            player.hand.append(random.choice(valid).copied())
        else:
            await player.dm("Oh no! You don't have any non-Victory cards!")
        player.update_hand()

class Villab(Action):
    desc = "+1-2 Cards\n+1-2 Actions\n(random)"
    cost = 4
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=random.randint(1,2)
        player.draw(random.randint(1,2))

class Gambler(Action):
    desc = "+1 Debt\nRoll a d6.\nChoose one: draw that many cards, or +1 Action."
    cost = 5
    async def play(self,game:Dominion,player:DPlayer):
        player.debt+=1
        roll = random.randint(1,6)
        if await game.yn_option(player,True,f"You rolled a {roll}! Draw that many cards?"):
            player.draw(roll)
        else:
            player.actions+=1
            player.update_hand()

class Antique(Treasure):
    desc = "£1-3\n(random)\n+1 Buy"
    cost = 4
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=random.randint(1,3)
        player.buys+=1
        player.update_hand()

class Santa(Action,Attack):
    desc = "+£2\nEach other player randomly gains a Silver or a Curse\n_have you been **naughty**?_"
    cost = 3
    async def bonus(self,game:Dominion,player:DPlayer):
        player.coins+=2
        player.update_hand()
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        if random.randint(0,1):
            await target.dm("You've been nice! Santa gives you a Silver!")
            await game.gain(target,Silver)
        else:
            await target.dm("You've been _naughty_! Santa gives you a Curse!")
            await game.gain(target,Curse)

class Inquisition(Action):
    desc = "Choose a card from your hand. Draw cards until you draw one of greater cost. If you didn't, gain an Epic Fail."
    cost = 6
    async def play(self,game:Dominion,player:DPlayer):
        if chosen:= await game.choose_card(player,player.hand[:],msg="Choose a card!"):
            target,others = common.deck_search(player,lambda c:c.get_cost(game,player)>chosen.get_cost(game,player))
            if target:
                player.hand.append(target)
            else:
                await game.gain(player,EpicFail)

    @classmethod
    def setup(cls, game: Dominion):
        game.add_nonsupply_pile(EpicFail)
cards = [Gambler,RogueScientist,Inquisition,Santa,Antique,Villab,GreyGoo]