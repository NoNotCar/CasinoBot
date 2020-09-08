import random

class Card(object):
    extype=[]
    info="N/A"
    o_name=""
    async def on_discard(self,game):
        pass
    def copy(self):
        return self.__class__()
    @property
    def name(self):
        return self.o_name or self.__class__.__name__
    @property
    def full_desc(self):
        return "%s [%s]: %s" % (self.name,", ".join(self.extype),self.info)
class Action(Card):
    extype = ["ACTION"]
    async def execute(self,game):
        if "DURATION" in self.extype:
            game.cp.durations.append(self)
class Bomb(Card):
    extype = ["BOMB"]
    async def execute(self,game):
        if "DURATION" in self.extype:
            game.cp.durations.append(self)
class Defuse(Card):
    extype = ["DEFUSE"]
    info="Defuse a bomb"
    async def execute(self,game,bomb):
        await game.cp.dm("Choose a position to put the bomb (0=top deck, %s=bottom deck)" % len(game.deck))
        n=await game.choose_number(game.cp,True,0,len(game.deck))
        game.deck.insert(n,bomb)
        if "DURATION" in self.extype:
            game.cp.durations.append(self)
class Duration(Card):
    def __init__(self):
        super().__init__()
        self.extype=self.extype[:]+["DURATION"]
    async def start_turn(self,game):
        pass
    async def end_turn(self,game):
        pass
class Attack(Card):
    def __init__(self):
        super().__init__()
        self.extype=self.extype[:]+["ATTACK"]
    async def execute(self,game,attacker=None):
        attacker=attacker or game.cp
        await game.channel.send("Choose another player to target!")
        target = await game.wait_for_tag(attacker,[p for p in game.survivors if p is not attacker])
        defence = await game.choose_card(target,[c for c in target.hand if isinstance(c,Defend)],False,"%s, either choose a Defend card to play or pass" % target.name)
        if defence:
            await game.channel.send("%s played %s" % (target.name,defence.full_desc))
            target.hand.remove(defence)
            await game.discard(defence)
        if not defence or not await defence.defend(game,target,attacker,self):
            await self.attack(game,target,attacker)
        else:
            await self.blocked(game, target,attacker)
    async def attack(self,game,target,attacker):
        if "DURATION" in self.extype:
            target.durations.append(self)
    async def blocked(self, game, target, attacker):
        pass
class Multiattack(Card):
    def __init__(self):
        super().__init__()
        self.extype=self.extype[:]+["MULTIATTACK"]
    async def execute(self,game,attacker=None):
        attacker=attacker or game.cp
        for target in [p for p in game.survivors if p is not attacker]:
            defence = await game.choose_card(target,[c for c in target.hand if isinstance(c,Defend)],False,"%s, either choose a Defend card to play or pass" % target.name)
            if defence:
                await game.channel.send("%s played %s" % (target.name,defence.full_desc))
                target.hand.remove(defence)
                await game.discard(defence)
            if not defence or not await defence.defend(game,target,attacker,self):
                await self.attack(game,target,attacker)
            else:
                await self.blocked(game, target,attacker)
    async def attack(self,game,target,attacker):
        if "DURATION" in self.extype:
            target.durations.append(self)
    async def blocked(self, game, target, attacker):
        pass
class Defend(Card):
    def __init__(self):
        super().__init__()
        self.extype = self.extype[:] + ["DEFEND"]
    async def defend(self,game,defender,attacker,attack:Attack):
        #Returns true if the defence was successful
        if isinstance(self,Duration):
            defender.durations.append(self)
        return True
class Dodge(Defend):
    info="Counter target attack"
class NoU(Defend):
    o_name = "No U"
    info="Redirect target attack at the attacker. They cannot defend."
    async def defend(self,game,defender,attacker,attack:Attack):
        await attack.execute(game,attacker)
        return True
class UnreliableBlock(Defend):
    info = "Has a 50% chance of countering target attack"
    async def defend(self,game,defender,attacker,attack:Attack):
        if random.randint(0,1):
            return True
        return False
class TrustyShield(Defend,Duration):
    info = "Counter target attack. At the start of your turn, return this to your hand."
    async def start_turn(self,game):
        game.cp.hand.append(self)
        game.cp.durations.remove(self)
        await game.channel.send("%s picks up their shield." % game.cp.name)
class Minefield(Defend):
    info = "Counter target attack. Add an Exploding Penguin to the top of the deck."
    async def defend(self,game,defender,attacker,attack:Attack):
        game.deck.insert(0,ExplodingPenguin())
        return True
class Mine(Defend):
    info = "Counter target attack. Add a copy of it to your hand"
    async def defend(self,game,defender,attacker,attack:Attack):
        defender.hand.append(attack.copy())
        return True
class SeizeControl(Defend):
    info = "Counter target attack. Take an extra turn."
    async def defend(self,game,defender,attacker,attack:Attack):
        game.next_turn=defender
        return True
class Nope(Defend,Defuse):
    info = "Counter target attack, or defuse a bomb."
class ExplodingPenguin(Bomb):
    info="You die."
    async def execute(self,game):
        await game.kill(game.cp)
class Shuffle(Action):
    info="Shuffle the deck"
    async def execute(self,game):
        random.shuffle(game.deck)
class EyeOfTheStorm(Action,Duration):
    info="At the start of your turn, shuffle the deck"
    async def start_turn(self,game):
        random.shuffle(game.deck)
class Skip(Action):
    info="End your turn"
    async def execute(self,game):
        await game.end_turn()
class TargetedSkip(Attack,Action):
    info="End your turn. Target player immediately takes a bonus turn."
    async def attack(self,game,target,attacker):
        game.next_turn=target
        await game.end_turn()
class SeeTheFuture(Action):
    info="View the top three cards of the deck"
    async def execute(self,game):
        await game.cp.dm("The top cards are: "+", ".join(c.name for c in game.deck[:3]))
class Radar(Action,Duration):
    info="At the start of your turn, view the top card of the deck"
    async def start_turn(self,game):
        await game.cp.dm("The top card is "+game.deck[0].name)
class Confidence(Action):
    info="Draw 2 cards"
    async def execute(self,game):
        await game.draw(2)
class Shoot(Attack,Action):
    info="Target player draws a card"
    async def attack(self,game,target,attacker):
        await game.draw(1,target)
class EMP(Bomb):
    info="Discard all duration cards in play"
    async def execute(self,game):
        for p in game.players:
            while p.durations:
                await game.discard(p.durations.pop())
class FluxRay(Attack,Action):
    info="Target player discards all duration cards in play"
    async def attack(self,game,target,attacker):
        while target.durations:
            await game.discard(target.durations.pop())
class TimeBomb(Bomb,Duration):
    info = "Die at the start of your next turn"
    async def start_turn(self,game):
        await game.kill(game.cp)
class IncendiaryGrenade(Bomb,Duration):
    info="At the start of your turn, discard a card"
    async def start_turn(self,game):
        await game.burn(game.cp)
class Flamethrower(Duration,Attack,Action):
    info="Target player discards a card at the start of their turn"
    async def start_turn(self,game):
        await game.burn(game.cp)
class Assassinate(Attack,Action):
    info = "Target player dies. If successfully defended, you die."
    async def attack(self,game,target,attacker):
        await game.kill(target)
    async def blocked(self, game, target,attacker):
        await game.kill(attacker)
class Reboot(Action):
    info = "End your turn. Take another turn."
    async def execute(self,game):
        game.next_turn=game.cp
        await game.end_turn()
class DelayTheInevitable(Action,Duration):
    info="End your turn. Take another turn after your next turn"
    async def execute(self,game):
        p=game.cp
        await game.end_turn()
        p.durations.append(self)
    async def end_turn(self,game):
        game.cp.durations.remove(self)
        await game.discard(self)
        game.next_turn=game.cp
class HalfAssedDefuse(Defuse,Duration):
    info="Die at the start of your next turn"
    async def start_turn(self,game):
        await game.kill(game.cp)
class TheWorldRevolving(Action,Duration):
    info="At the start of your turn, you may choose to put the top card of the deck on the bottom"
    async def start_turn(self,game):
        if await game.choose_option(game.cp, False, ["yes","no"],"Revolve the world? (yes, no)",secret=True)=="yes":
            game.deck.append(game.deck.pop())
class DejaVu(Action):
    info="Put your hand on top of the deck in a random order"
    async def execute(self,game):
        random.shuffle(game.cp.hand)
        game.deck=game.cp.hand+game.deck
        game.cp.hand=[]
class Prophet(Action):
    info="Reveal the top card of the deck"
    async def execute(self,game):
        await game.channel.send("The top card is " + game.deck[0].name)
class TimeToStop(Action):
    info = "Discard all duration cards in play"
    async def execute(self, game):
        for p in game.players:
            while p.durations:
                await game.discard(p.durations.pop())
class HighIQPlay(Action):
    info="Draw a card for each duration in play. End your turn"
    async def execute(self,game):
        await game.draw(sum(len(p.durations) for p in game.survivors))
        await game.end_turn()
class Necromancy(Action):
    info="You may draw a card from the discard pile"
    async def execute(self,game):
        chosen=await game.choose_card(game.cp,game.discards)
        if chosen:
            await game.draw_card(game.cp,chosen)
class EmergencyDefuse(Defuse):
    info="Discard your hand"
    async def execute(self,game,bomb):
        await super().execute(game,bomb)
        while game.cp.hand:
            await game.discard(game.cp.hand.pop())
class Escalate(Defuse):
    info="Put a copy of the defused card on top of the deck"
    async def execute(self,game,bomb):
        await super().execute(game,bomb)
        game.deck.insert(0,bomb.copy())
class Call999(Action):
    info="Discard the top card of the deck. If it's not a bomb, you die."
    async def execute(self,game):
        top=game.deck.pop(0)
        await game.discard(top)
        if "BOMB" not in top.extype:
            await game.channel.send("It wasn't a bomb! Too bad!")
            await game.kill(game.cp)
class Favour(Attack,Action):
    info="Target player gives you a card of their choice"
    async def attack(self,game,target,attacker):
        if target.hand:
            taken = await game.choose_card(target, target.hand, True, "Choose a card to generously donate")
            target.hand.remove(taken)
            attacker.hand.append(taken)
            await attacker.dm("You were given %s" % taken.name)
            return True
        else:
            await game.channel.send("TOO BAD! %s has no cards!" % target.name)
            return False
class CashMoney(Favour):
    info="Target player gives you a card of their choice. They gain a copy of this card"
    async def attack(self,game,target,attacker):
        if await super().attack(game,target,attacker):
            target.hand.append(CashMoney())
class Tax(Duration,Favour):
    taxer=None
    info="Target player gives you a card of their choice at the start of their turn. If they can't, discard this."
    async def attack(self,game,target,attacker):
        self.taxer=attacker
    async def start_turn(self,game):
        await game.channel.send("%s must pay tax to %s!" % (game.cp.name,self.taxer.name))
        if not await super().attack(game,game.cp,self.taxer):
            game.cp.durations.remove(self)
            await game.discard(self)
class Grovel(Favour):
    info="Discard your hand. %s." % Favour.info
    async def attack(self,game,target,attacker):
        while attacker.hand:
            await game.discard(attacker.hand.pop())
        await super().attack(game,target,attacker)
class Steal(Attack,Action):
    info="Gain a random card from target player's hand"
    async def attack(self,game,target,attacker):
        if target.hand:
            taken=random.choice(target.hand)
            target.hand.remove(taken)
            attacker.hand.append(taken)
            await target.dm("%s was stolen!" % taken.name)
            await attacker.dm("You stole %s!" % taken.name)
        else:
            await game.channel.send("TOO BAD! %s has no cards!" % target.name)
class Spy(Attack,Action):
    info = "Look at target player's hand"
    async def attack(self,game,target,attacker):
        await attacker.dm("Target's hand: "+", ".join(c.name for c in target.hand))
class Birthday(Multiattack,Favour):
    info = "All other players give you a card of their choice."
    async def attack(self,game,target,attacker):
        await Favour.attack(self,game,target,attacker)
class Revolution(Multiattack,Action):
    info = "All other players must discard a card"
    async def attack(self,game,target,attacker):
        await game.burn(target,"%s must discard a card")
class WallOfWind(Defend):
    info = "Counter target attack. Shuffle the deck"
    async def defend(self,game,defender,attacker,attack:Attack):
        random.shuffle(game.deck)
        return True
basedeck=[SeeTheFuture,Favour,Skip,TargetedSkip]*4+\
         [Radar,EmergencyDefuse,Reboot,Confidence,HighIQPlay,Prophet,Steal,Shuffle,Shoot,Dodge,UnreliableBlock,Minefield,Spy,Grovel,Birthday,Revolution,NoU]*2+\
         [Necromancy,TimeToStop,Call999,HalfAssedDefuse,DejaVu,Flamethrower,TrustyShield,Assassinate,TheWorldRevolving,Tax,CashMoney,FluxRay,Nope,SeizeControl,Escalate,WallOfWind,EyeOfTheStorm]
spbombs=[EMP,TimeBomb,IncendiaryGrenade]
