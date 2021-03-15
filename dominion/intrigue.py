from .base import *
from . import common
from .vanilla import Vanilla,Cantrip,Village
class Courtyard(Action):
    cost = 2
    desc="+3 Cards\nPut a card from your hand onto your deck."
    async def play(self,game:Dominion,player:DPlayer):
        player.draw(3)
        player.deck.dump(await game.choose_cards(player,player.hand,1,1,"Choose a card to topdeck."))
class Lurker(Action):
    cost = 2
    desc = "Choose one: Trash an Action from the Supply, or gain an Action from the trash"
    async def play(self,game:Dominion,player:DPlayer):
        if (await game.choose_option(player,True,["trash","gain"]))=="trash":
            target = await game.choose_card(player,[s.top for s in game.supplies.values() if "ACTION" in s.top.extype],msg="Choose an Action to trash from the Supply")
            if target:
                for s in game.supplies:
                    if s.top==target:
                        await game.trash(player,s.take())
                        return
        else:
            gainable = [c for c in game.trashpile.contents if "ACTION" in c.extype]
            gain = await game.choose_card(player,gainable,msg=f"Choose an action to gain from the Trash!\nAvailable: {dib.smart_list([c.name for c in gainable])}")
            if gain:
                game.trashpile.contents.remove(gain)
                player.discard.add(gain)
class Masquerade(Action):
    cost = 3
    desc = "+2 Cards\nEach player with any cards in hand passes one to the next such player (in turn order), at once. Then you may trash a card from your hand."
    async def play(self,game:Dominion,player:DPlayer):
        player.draw(2)
        masquerading = [p for p in game.players if p.hand]
        passing = await dib.gather([game.choose_card(p,p.hand,msg="Choose a card to pass!") for p in masquerading])
        for n,p in enumerate(passing):
            masquerading[(n+1)%len(masquerading)].hand.append(p)
        for m in masquerading:
            m.update_hand()
        if trashing:=await game.choose_card(player,player.hand,True,"Choose a card to trash, or pass."):
            await game.trash(player,trashing)

class ShantyTown(Action):
    cost = 3
    override_name = "Shanty Town"
    desc = "+2 Actions\nIf you have no Actions, +2 Cards"
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=2
        if not any(isinstance(c,Action) for c in player.hand):
            player.draw(2)
        else:
            player.update_hand()
class Steward(Action):
    cost = 3
    desc = "Choose one: +2 Cards, +£2, trash 2 cards from your hand."
    async def play(self,game:Dominion,player:DPlayer):
        option = await game.choose_option(player,True,["cards","money","trash"])
        if option=="cards":
            player.draw(2)
        elif option=="money":
            player.coins+=1
            player.update_hand()
        else:
            await common.trash_from_hand(game,player,2,2)
class Swindler(Action,Attack):
    cost = 3
    desc = "+£2\nEach other player trashes the top card of their deck and gains a card with the same cost that you choose."
    async def bonus(self,game:Dominion,player:DPlayer):
        player.coins+=2
        player.update_hand()
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        trashing = target.xdraw(1)
        if trashing:
            trashing=trashing[0]
            valid = [s.top for c, s in game.supplies.items() if s and s.top.get_cost(game,target)==trashing.get_cost(game,target)]
            if valid:
                chosen = await game.choose_card(attacker, valid, msg=f"{target.name} trashed a {trashing.name}. Choose a card costing {trashing.get_cost(game,target)} for them to gain!")
                await game.gain(target, chosen.__class__)
                target.update_hand()
                await game.send(f"{target.name} gained a {chosen.name}!")
            else:
                await attacker.dm(f"{target.name} trashed a {trashing.name}, but there were no valid cards for them to gain...")
class WishingWell(Cantrip):
    cost = 3
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        try:
            top = player.xdraw(1)[0]
            named = await game.wait_for_text(player,"Name the top card of your deck!")
            if named==top.name.lower():
                await player.dm("CORRECT!")
                player.hand.append(top)
                player.update_hand()
            else:
                await player.dm(f"Sorry, your top card was actually {top.name}")
                player.deck.add(top)
        except IndexError:
            await player.dm("You've drawn your entire deck and so can't wish...")
    @property
    def desc(self):
        return super().desc+"\nName the top card of your deck and draw it if you're correct."
class Baron(Action):
    cost = 4
    desc = "+1 Buy\nYou may discard an Estate for +£4. If you don't, gain an Estate."
    async def play(self,game:Dominion,player:DPlayer):
        player.buys+=1
        if any(isinstance(c,Estate) for c in player.hand) and await game.yn_option(player,True,"You have an Estate! Discard it?"):
            target = next(c for c in player.hand if isinstance(c,Estate))
            player.hand.remove(target)
            await game.discard(player,target)
            player.coins+=4
        else:
            await game.gain(player,Estate)
        player.update_hand()
class Conspirator(Action):
    cost = 4
    desc = "+$2\nIf you’ve played 3 or more Actions this turn (counting this), +1 Card and +1 Action."
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=2
        if player.actions_played>=3:
            player.actions+=1
            player.draw(1)
        else:
            player.update_hand()
class Ironworks(Action):
    cost = 4
    desc = "Gain a card costing up to $4.\nIf the gained card is an…\nAction card, +1 Action\nTreasure card, +$1\nVictory card, +1 Card"
    async def play(self,game:Dominion,player:DPlayer):
        c = await common.cost_limited_gain(game,player,4)
        if c:
            if isinstance(c,Action):
                player.actions+=1
            if isinstance(c,Treasure):
                player.coins+=1
            if isinstance(c,Victory):
                player.draw(1)
            else:
                player.update_hand()
class MiningVillage(Village):
    cost = 4
    extra_desc = "You may trash this. If you did, +£2"
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        if self in player.active and await game.yn_option(player,True,"Trash this?"):
            player.coins+=2
            player.update_hand()
            player.active.remove(self)
            game.trash(player,self)
class SecretPassage(Vanilla):
    cost = 4
    draw = 2
    actions = 1
    extra_desc = "Put a card from your hand anywhere in your deck"
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        if target:=await game.choose_card(player,player.hand,msg="Choose a card to insert."):
            pos = await game.choose_number(player,True,0,len(player.deck),f"Choose a position (0=bottomdeck, {len(player.deck)}=topdeck")
            player.deck.contents.insert(pos,target)
            player.update_hand()
class Duke(Victory):
    cost = 5
    desc = "Worth 1VP per Duchy you have."
    def final_vp(self,game:Dominion,player:DPlayer):
        return len([c for c in player.all_cards if isinstance(c,Duchy)])
class Minion(Action,Attack):
    cost = 5
    desc = "+1 Action\nChoose one: +$2; or discard your hand, +4 Cards, and each other player with at least 5 cards in hand discards their hand and draws 4 cards."
    async def play(self,game:Dominion,player:DPlayer):
        player.actions+=1
        if (await game.choose_option(player,True,["money","attack"]))=="money":
            player.coins+=2
            player.update_hand()
        else:
            await super().play(game,player)
    async def bonus(self,game:Dominion,player:DPlayer):
        player.discard.dump(player.hand)
        player.draw(4)
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        if len(target.hand)>=5:
            await self.bonus(game,target)
class Patrol(Action):
    cost = 5
    desc = "+3 Cards\nDraw any Victory or Defeat cards in the top 4 cards of your deck."
    async def play(self,game:Dominion,player:DPlayer):
        player.draw(3)
        revealed = player.xdraw(4)
        vds = [r for r in revealed if isinstance(r,Victory) or isinstance(r,Defeat)]
        player.hand.extend(vds)
        player.deck.dump([r for r in revealed if r not in vds])
        player.update_hand()
class Replace(Action,Attack):
    cost = 5
    desc = "Trash a card from your hand. Gain a card costing up to $2 more than it. If the gained card is an Action or Treasure, put it onto your deck; if it's a Victory card, each other player gains a Curse."
    async def play(self,game:Dominion,player:DPlayer):
        if gained:=await common.remodel(game,player,2):
            if isinstance(gained,Treasure) or isinstance(gained,Action):
                player.deck.add(player.discard.take())
            elif isinstance(gained,Victory):
                await super().play(game,player)
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        await game.gain(target,Curse)
class Torturer(Action,Attack):
    cost = 5
    desc = "+3 Cards\nEach other player either discards 2 cards or gains a Curse to their hand, their choice. (They may pick an option they can't do.)"
    async def bonus(self,game:Dominion,player:DPlayer):
        player.draw(3)
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        if await game.yn_option(target,True,"Would you like to gain a Curse?"):
            await game.gain(target,Curse,"hand")
        else:
            target.discard(await game.choose_cards(target,target.hand,2,2,"Choose 2 cards to discard then."))
class TradingPost(Action):
    cost = 5
    desc = "Trash 2 cards from your hand. If you did, gain a Silver to your hand."
    async def play(self,game:Dominion,player:DPlayer):
        trashing = await common.trash_from_hand(game,player,2,2)
        if len(trashing)==2:
            await game.gain(player,Silver,"hand")
class Upgrade(Cantrip):
    cost = 5
    extra_desc = "Trash a card from your hand. Gain a card costing exactly £1 more than it."
    async def play(self,game:Dominion,player:DPlayer):
        await super().play(game,player)
        await common.remodel(game,player,1,True)

class Harem(SimpleTreasure,Victory):
    income = 2
    vp = 2
    cost = 6
    desc = "£2\n2VP"

class Nobles(Action,Victory):
    cost = 6
    vp=2
    desc = "Choose one: +3 Cards; or +2 Actions.\n2VP"
    async def play(self,game:Dominion,player:DPlayer):
        if (await game.choose_option(player,True,["cards","actions"]))=="cards":
            player.draw(3)
        else:
            player.actions+=2
            player.update_hand()

class Coppersmith(Action,Reaction):
    cost = 4
    desc = "When you play a copper this turn, +£1"
    async def play(self,game:Dominion,player:DPlayer):
        player.reactions["play Copper"].append(self)
    async def react(self,game:Dominion,player:DPlayer,event:str,**kwargs):
        player.coins+=1
class Diplomat(Action,Reaction):
    cost = 4
    hand="attacked"
    desc = "+2 Cards\nIf you have 5 or fewer cards in hand (after drawing), +2 Actions.\nWhen another player plays an Attack card, you may first reveal this from a hand of 5 or more cards, to draw 2 cards then discard 3."
    async def play(self,game:Dominion,player:DPlayer):
        if len(player.hand)<=3:
            player.actions+=2
        player.draw(2)
    async def react(self,game:Dominion,player:DPlayer,event:str,**kwargs):
        if len(player.hand)>=5 and await game.yn_option(player,True,f"You're being attacked by a {kwargs['card'].name}! React with Diplomat?"):
            player.draw(2)
            player.discard.dump(await game.choose_cards(player,player.hand,3,3,"Choose 3 cards to discard"))
cards = [Courtyard,Lurker,Masquerade,ShantyTown,Steward,Swindler,WishingWell,Baron,
         Conspirator,Ironworks,MiningVillage,SecretPassage,Duke,Minion,Patrol,Replace,
         Torturer,TradingPost,Upgrade,Harem,Nobles,Coppersmith,Diplomat]



