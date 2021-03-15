from __future__ import annotations

import importlib

import dib
import typing
import random
import asyncio
import collections
import re
from functools import total_ordering
def camel_case_split(s:str)->str:
    return " ".join(re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', s))
def substrings(s:str):
    split = s.split()
    for n,s in enumerate(split):
        yield " ".join(split[:n+1])
@total_ordering
class Cost(object):
    def __init__(self,coins:typing.Union[int,Cost]=0,potions=0,debt=0):
        if isinstance(coins,Cost):
            self.coins=coins.coins
            self.potions=coins.potions
            self.debt=coins.debt
        else:
            self.coins = coins
            self.potions = potions
            self.debt=debt
    def __str__(self):
        s=""
        if self.coins:
            s+=f"£{self.coins}"
        if self.potions:
            s+="P"*self.potions
        if self.debt:
            s+=f"D{self.debt}"
        return s
    def __eq__(self, other):
        if isinstance(other, Cost):
            return (self.coins, self.potions, self.debt) == (other.coins, other.potions, other.debt)
        else:
            return self > Cost(other)
    def __lt__(self, other):
        if isinstance(other,Cost):
            return (self.coins,self.potions,self.debt)<(other.coins,other.potions,other.debt)
        else:
            return self>Cost(other)
    def __add__(self, other):
        if isinstance(other,Cost):
            return Cost(self.coins+other.coins,self.potions+other.potions,self.debt+other.debt)
        else:
            return Cost(self.coins+other,self.potions,self.debt)
class Card(object):
    cost = 0
    supply = True
    total = 10
    extype = ()
    override_name = ""
    desc = ""
    async def play(self,game:Dominion,player:DPlayer):
        pass
    def on_draw(self,player:DPlayer):
        pass
    def get_cost(self,game:Dominion,player:DPlayer):
        return self.cost
    def buyable(self,game:Dominion,player:DPlayer):
        return self.get_cost(game,player)<=player.coins+player.coffers-player.debt
    async def on_buy(self,game:Dominion,player:DPlayer):
        return False
    async def on_gain(self,game:Dominion,player:DPlayer):
        return False
    async def on_trash(self, game: Dominion, player: DPlayer):
        pass
    async def react(self,game:Dominion,player:DPlayer,event:str,**kwargs):
        pass
    def should_discard(self):
        return True
    @classmethod
    def get_supply(cls,players:int):
        return cls.total
    @classmethod
    def setup(cls,game:Dominion):
        pass
    @classmethod
    def teardown(cls,game:Dominion):
        pass
    @property
    def name(self):
        return self.override_name or camel_case_split(self.__class__.__name__)
    @property
    def supply_text(self):
        return f"{self.name}: £{self.cost}"
    @property
    def full_desc(self):
        return f"{self.supply_text}\n{self.desc}\n[{' '.join(self.extype)}]"
    def __repr__(self):
        return self.name
class CardPile(object):
    def __init__(self,secret=False,contents=()):
        self.secret = secret
        self.contents = list(contents)
    def add(self,card:Card):
        self.contents.append(card)
        return card
    def dump(self,cards:typing.List[Card]):
        self.contents.extend(cards)
        cards.clear()
    def shuffle(self):
        random.shuffle(self.contents)
    def take(self):
        return self.contents.pop(-1)
    def draw_all(self,f:typing.Callable[[Card],bool]=lambda c:True):
        taking = []
        for c in self.contents[:]:
            if f(c):
                self.contents.remove(c)
                taking.append(c)
        return taking
    def view(self):
        return dib.smart_list([c.name for c in self.contents])
    def __bool__(self):
        return bool(self.contents)
    def __len__(self):
        return len(self.contents)
    def __contains__(self, item):
        return item in self.contents
    @property
    def empty(self):
        return not self.contents
    @property
    def top(self):
        return self.contents[-1]
    @property
    def bottom(self):
        return self.contents[0]
class SupplyPile(CardPile):
    def __init__(self,card:typing.Type[Card],players:int):
        self.card = card
        super().__init__(False,tuple(card() for _ in range(card.get_supply(players))))
        self.sname = self.contents[0].name
    @property
    def text(self):
        return f"[{self.sname}: £{self.card.cost} ({len(self.contents)})]"
class Treasure(Card):
    auto_order = 0
    def __init__(self):
        super().__init__()
        self.extype = self.extype + ("TREASURE",)
class SimpleTreasure(Treasure):
    income = 1
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=self.income
class Copper(SimpleTreasure):
    total = 60
class Silver(SimpleTreasure):
    income = 2
    cost = 3
    total = 40
class Gold(SimpleTreasure):
    income = 3
    cost = 6
    total = 30
class Platinum(SimpleTreasure):
    income = 5
    cost = 9
    total = 12
class VP(Card):
    def final_vp(self, game: Dominion, player: DPlayer):
        return 0
class Victory(VP):
    vp = 1
    def __init__(self):
        super().__init__()
        self.extype=self.extype+("VICTORY",)
    def final_vp(self,game:Dominion,player:DPlayer):
        return self.vp
    @classmethod
    def get_supply(cls, players: int):
        return 8 if players==2 else 12
class Defeat(VP):
    def __init__(self):
        super().__init__()
        self.extype=("DEFEAT",)+self.extype
class Action(Card):
    def __init__(self):
        super().__init__()
        self.extype=("ACTION",)+self.extype
class Night(Card):
    def __init__(self):
        super().__init__()
        self.extype=("NIGHT",)+self.extype
class Reaction(Card):
    hand = ""
    def __init__(self):
        super().__init__()
        self.extype=("REACTION",)+self.extype
class Duration(Card):
    trigger = "start"
    discard_now = False
    def __init__(self):
        super().__init__()
        self.extype = ("DURATION",) + self.extype
    async def first(self,game:Dominion,player:DPlayer):
        pass
    async def next(self,game:Dominion,player:DPlayer):
        pass
    async def react(self,game:Dominion,player:DPlayer,event:str,**kwargs):
        await self.next(game,player)
        self.discard_now=True
    async def play(self,game:Dominion,player:DPlayer):
        self.discard_now=False
        player.reactions[self.trigger].append(self)
        await self.first(game,player)
    def should_discard(self):
        return self.discard_now
class Attack(Card):
    def __init__(self):
        super().__init__()
        self.extype=("ATTACK",)+self.extype
    async def play(self,game:Dominion,player:DPlayer):
        await self.bonus(game,player)
        for p in game.attack_order(player):
            blocked=False
            await p.react(game, "attacked", card=self)
            for c in p.hand+p.active:
                if isinstance(c,Defence):
                    if await c.on_block(game,player,p):
                        await game.send(f"{p.name} blocked with {c.name}!")
                        blocked=True
            if not blocked:
                await self.attack(game, p, player)
    async def bonus(self,game:Dominion,player:DPlayer):
        pass
    async def attack(self, game: Dominion, target: DPlayer, attacker:DPlayer):
        pass
class Defence(Card):
    def __init__(self):
        super().__init__()
        self.extype = ("DEFENCE",)+ self.extype
    async def on_block(self,game:Dominion,attacker:DPlayer,targeted:DPlayer):
        return True
class Curse(Defeat):
    def final_vp(self, game: Dominion, player: DPlayer):
        return -1
class Estate(Victory):
    cost = 2
class Duchy(Victory):
    vp = 3
    cost = 5
class Province(Victory):
    vp = 6
    cost = 8
    @classmethod
    def get_supply(cls,players:int):
        return players*4 if players<4 else players*3
class Colony(Province):
    vp = 10
    cost = 11
class DPlayer(dib.BasePlayer):
    coins = 0
    coffers = 0
    debt = 0
    actions = 1
    villagers = 0
    buys = 1
    marketeers = 0
    vp = 0
    handmsg = None
    actions_played=0
    def __init__(self,p,f=False):
        super().__init__(p,f)
        self.hand = []
        self.active = []
        self.exiled = []
        self.deck = CardPile(True)
        self.discard = CardPile()
        self.reactions = collections.defaultdict(list)
        self.handlock = asyncio.Lock()
    def update_hand(self,resend=False):
        new = ("Your hand: "+", ".join(c.name for c in self.hand)) if self.hand else "Your hand is empty!"
        new+=f"\nActions: {self.actions}, Villagers: {self.villagers}, Buys: {self.buys}, Coins: {self.coins}, Coffers: {self.coffers}, Debt: {self.debt}, VP: {self.vp}"
        new+=f"\nDECK: {len(self.deck)}, DISCARD: {len(self.discard)}"
        asyncio.create_task(self.update_handmsg(new,resend))
    async def update_handmsg(self,new:str,resend=False):
        async with self.handlock:
            if not self.handmsg or resend:
                self.handmsg=await self.dm(new)
            else:
                await self.handmsg.edit(content=new)
    def xdraw(self,n=1)->typing.List[Card]:
        cards = []
        for x in range(n):
            if not self.deck:
                asyncio.create_task(self.dm("Out of deck, reshuffling!"))
                while self.discard:
                    self.deck.add(self.discard.take())
                if self.deck:
                    self.deck.shuffle()
                else:
                    return cards
            cards.append(self.deck.take())
        return cards
    def draw(self,n=1):
        cards = self.xdraw(n)
        self.draw_cards(cards)
        return cards
    def draw_cards(self,cards:typing.List[Card]):
        if cards:
            self.hand.extend(cards)
            self.update_hand()
        for c in cards:
            c.on_draw(self)
    def redraw(self,update=True):
        self.discard.dump(self.hand)
        for a in self.active[:]:
            if a.should_discard():
                self.discard.add(a)
                self.active.remove(a)
        for r,l in self.reactions.items():
            self.reactions[r]=[c for c in l if c in self.active]
        self.draw(5)
        self.actions=1
        self.coins=0
        self.buys=1
        self.actions_played=0
        if update:
            self.update_hand(True)
    async def react(self,game:Dominion,event:str,**kwargs):
        for e in substrings(event):
            for c in self.reactions[e][:]:
                if await c.react(game,self,e,**kwargs):
                    self.reactions[e].remove(c)
            for c in self.hand[:]:
                if isinstance(c,Reaction) and c.hand==e:
                    await c.react(game,self,e,**kwargs)
    @property
    def all_cards(self):
        return self.hand+self.discard.contents+self.deck.contents+self.active+self.exiled
BASIC = [Curse,Estate,Duchy,Province,Copper,Silver,Gold,Platinum,Colony]
EXPANSIONS = ["vanilla","unhinged","unbound","intrigue","contests","seaside","prosperity","cornucopia"]
class Dominion(dib.BaseGame):
    name = "dominion"
    min_players = 2
    max_players = 6
    playerclass = DPlayer
    phase = "ACTION"
    no_pump = False
    has_ai = True
    def __init__(self,ctx):
        super().__init__(ctx)
        self.supplies = {}
        self.nonsupplies = {}
        self.trashpile = CardPile()
    def add_supply_pile(self,card:typing.Type[Card]):
        self.supplies[card]=SupplyPile(card,len(self.players))
        card.setup(self)
    def add_nonsupply_pile(self,card:typing.Type[Card]):
        self.nonsupplies[card] = SupplyPile(card, len(self.players))
    async def gain(self,player:DPlayer,card:typing.Type[Card],destination = "discard",cloned=False,suppress_msg=False):
        if cloned:
            return player.discard.add(card())
        if supply:=(self.supplies.get(card,None) or self.nonsupplies.get(card,None)):
            if not supply.empty:
                card = supply.take()
                if alt_dest:=await card.on_gain(self,player) and destination=="discard":
                    destination=alt_dest
                if destination=="discard":
                    player.discard.add(card)
                elif destination=="hand":
                    player.hand.append(card)
                    player.update_hand()
                elif destination=="topdeck":
                    player.deck.add(card)
                await player.react(self,f"gain {card.name}",card=card)
                could_release = [e for e in player.exiled if isinstance(e,card.__class__)]
                if could_release and await self.yn_option(player,True,f"Release {len(could_release)} cards from exile?"):
                    for c in could_release:
                        player.exiled.remove(c)
                    player.discard.dump(could_release)
                if not suppress_msg:
                    await self.send(f"{player.name} gained a {card.name}!")
                return card
            elif not suppress_msg:
                await self.send(f"{player.name} couldn't gain a {card().name}, since the pile's empty!")
        if not suppress_msg:
            await self.send(f"{player.name} couldn't gain a {card().name}, since it's not in the Supply!")
        return False
    async def choose_cards(self,player:DPlayer,cards:typing.Union[typing.List[Card],CardPile],mn=0,mx=99,msg="",private=True):
        if isinstance(cards,CardPile):
            cards=cards.contents
        mn = min(mn,len(cards))
        mx=  min(mx,len(cards))
        if mn==len(cards):
            result = cards[:]
            cards.clear()
            return result
        if mx<=0:
            return []
        while True:
            if player.fake:
                taking = random.randint(mn,mx)
                if taking==0:
                    inp="pass"
                else:
                    inp= ", ".join(c.name for c in random.sample(cards,random.randint(mn,mx)))
            else:
                inp = await self.wait_for_text(player,msg,private)
            if inp.lower()=="pass" and mn==0:
                return []
            cnames = [n.strip().lower() for n in inp.split(",")]
            selected = []
            for n in cnames:
                if matching:=self.parse_card(n,cards):
                    selected.append(matching)
                    cards.remove(matching)
                else:
                    await (player.dm if private else self.send)("Invalid card: %s" % n)
                    cards.extend(selected)
                    break
            else:
                if cards is player.hand:
                    player.update_hand()
                return selected
    def parse_card(self,i:str,cards:typing.List[Card]):
        try:
            return next(c for c in cards if c.name.lower() == i)
        except StopIteration:
            return None
    async def choose_card(self,player:DPlayer,cards:typing.List[Card],can_pass = False,msg="",private=True):
        result = await self.choose_cards(player,cards,0 if can_pass else 1,1,msg,private)
        if result:
            return result[0]
        return None
    async def play_card(self,player:DPlayer,card:Card,already_removed=False):
        if card in player.hand or already_removed:
            if card in player.hand:
                player.hand.remove(card)
            if card not in player.active:
                player.active.append(card)
        if self.phase=="ACTION":
            player.actions_played+=1
        await self.send(f"{player.name} played a {card.name}!")
        await player.react(self,f"played {card.name}")
        await card.play(self,player)
        player.update_hand()
    async def trash(self,player:DPlayer,cards:typing.Union[Card,typing.List[Card]]):
        if isinstance(cards,Card):
            cards=[cards]
        for c in cards:
            await c.on_trash(self,player)
            await player.react(self,f"trashed {c.name}",card=c)
        await self.send(f"{player.name} trashed a {dib.smart_list([c.name for c in cards])}!")
        self.trashpile.dump(cards)
    async def exile(self,player:DPlayer,cards:typing.Union[Card,typing.List[Card]]):
        if isinstance(cards,Card):
            cards=[cards]
        for c in cards:
            await c.on_trash(self,player)
            await player.react(self,f"exiled {c.name}",card=c)
        await self.send(f"{player.name} exiled a {dib.smart_list([c.name for c in cards])}!")
        player.exiled.extend(cards)
    async def discard(self,player:DPlayer,cards:typing.Union[Card,typing.List[Card]]):
        if isinstance(cards,Card):
            cards=[cards]
        await self.send(f"{player.name} discarded a {dib.smart_list([c.name for c in cards])}!")
        player.discard.dump(cards)
    def view_supplies(self):
        kingdom = sorted((s for c,s in self.supplies.items() if c not in BASIC),key=lambda s:s.card.cost)
        s = f"""SUPPLIES
{"".join(s.text for c,s in self.supplies.items() if c in BASIC)}
KINGDOM CARDS
{"".join(s.text for s in kingdom[:5])}
{"".join(s.text for s in kingdom[5:])}"""
        if self.nonsupplies:
            s+=f"\nNON-SUPPLY CARDS\n{''.join(s.text for s in self.nonsupplies.values())}"
        return s
    async def autoplay_treasures(self,player:DPlayer):
        await player.dm("Autoplaying Treasures...")
        while treasures:= [c for c in player.hand if isinstance(c,Treasure)]:
            target = min(treasures,key=lambda c:c.auto_order)
            await self.play_card(player,target)
    async def ai_action(self,player:DPlayer):
        if self.phase=="ACTION":
            await self.autoplay_treasures(player)
            money = player.coins+player.coffers-player.debt
            if Colony in self.supplies:
                if money>=11:
                    return "buy colony"
                elif money>=9:
                    return "buy platinum"
            elif money>=8:
                return "buy province"
            if money>=6:
                return "buy gold"
            elif money>=3:
                return "buy silver"
        return "pass"
    async def payoff_debt(self,p:DPlayer,auto_coffers = False):
        if p.debt:
            coffers = 0
            if p.coins<p.debt:
                if auto_coffers:
                    coffers=p.coffers
                elif p.coffers:
                    coffers = await self.choose_number(p, True, 0, min(p.coffers, p.debt - p.coins),
                                                       "Choose how many coffers to use to pay off debt!")
            old_debt = p.debt
            p.debt -= min(p.debt,coffers + p.coins)
            p.coffers -= coffers
            p.coins -= min(old_debt, p.coins)
            p.update_hand()
        else:
            await p.dm("You don't have any debt to pay off!")
    async def run(self,*modifiers):
        if not modifiers:
            modifiers=["vanilla"]
        elif modifiers[0]=="all":
            modifiers=EXPANSIONS
        kingdoms = []
        for m in modifiers:
            if m in EXPANSIONS:
                kingdoms.extend(importlib.import_module(f"dominion.{m}").cards)
        for basic in BASIC[:7]:
            self.add_supply_pile(basic)
        random.shuffle(kingdoms)
        for kc in kingdoms[:10]:
            self.add_supply_pile(kc)
        if sum(kc.cost for kc in kingdoms[:10])/10>4.5:
            self.add_supply_pile(Platinum)
            self.add_supply_pile(Colony)
        self.info={s().name.lower():s().full_desc for s in self.supplies}
        for p in self.players:
            for _ in range(7):
                await self.gain(p,Copper,cloned=True)
            for _ in range(3):
                await self.gain(p,Estate,cloned=True)
            p.redraw(False)
        random.shuffle(self.players)
        while True:
            await self.send(self.view_supplies())
            for p in self.players:
                if not p.fake:
                    await p.dm(self.view_supplies())
                    await self.send(f"{p.tag}, it's your turn!")
                await p.react(self,"start")
                self.phase = "ACTION"
                while True:
                    if not p.fake:
                        i = (await self.wait_for_text(p,"Choose a card to play/buy, or pass",validation=lambda t:len(t) and t[0]!="$")).lower()
                    else:
                        i=await self.ai_action(p)
                    if i=="pass":
                        await self.send(f"{p.name} has passed!")
                        break
                    first = i.split()[0]
                    if first=="resend":
                        p.update_hand(True)
                    elif first=="autoplay":
                        if self.phase=="NIGHT":
                            await p.dm("Can't autoplay Treasures, it's nighttime!")
                        else:
                            await self.autoplay_treasures(p)
                            self.phase = "TREASURE"
                    elif first=="debt":
                        if self.phase == "NIGHT":
                            await p.dm("Can't pay off debt, it's nighttime!")
                        else:
                            await self.autoplay_treasures(p)
                            self.phase = "TREASURE"
                        await self.payoff_debt(p)
                    elif first=="buy":
                        if self.phase=="ACTION":
                            await self.autoplay_treasures(p)
                            self.phase="TREASURE"
                        elif self.phase=="NIGHT":
                            await p.dm("Can't buy anything, it's nighttime!")
                            continue
                        if p.buys>0:
                            try:
                                to_buy = i.split(maxsplit=1)[1]
                                if buying:=self.parse_card(to_buy,[s.top for s in self.supplies.values() if s]):
                                    if buying.buyable(self,p):
                                        total_cost = buying.cost+p.debt
                                        p.debt = 0
                                        p.coffers-=max(0,total_cost-p.coins)
                                        p.coins-=min(total_cost,p.coins)
                                        p.buys-=1
                                        await p.react(self,f"buy {buying.name}",card=buying)
                                        await buying.on_buy(self,p)
                                        await self.gain(p,buying.__class__,suppress_msg=True)
                                        await p.dm(f"Buying successful!")
                                        await self.send(f"{p.name} bought a {buying.name}!")
                                        if not p.buys or any(isinstance(c,Night) for c in p.hand):
                                            await p.dm("No Buys or Nights left, automatically ending turn!")
                                            break
                                        else:
                                            p.update_hand()
                                    else:
                                        await p.dm("You don't have enough CASH MONEY to buy that!")
                                else:
                                    await p.dm("%s is not available to buy, sorry!" % to_buy)
                            except IndexError:
                                await p.dm("Buy WHAT???")
                        else:
                            await p.dm("Sorry, you're out of Buys!")
                    elif to_play:=self.parse_card(i,p.hand):
                        porder = ["ACTION","TREASURE","NIGHT"]
                        try:
                            self.phase=next(e for e in to_play.extype if e in porder and (porder.index(e)>=porder.index(self.phase)))
                            if self.phase=="ACTION":
                                if not (p.actions or p.villagers):
                                    await p.dm("You don't have any actions or villagers left!")
                                    continue
                                else:
                                    if p.actions:
                                        p.actions-=1
                                    else:
                                        p.villagers-=1
                                    p.update_hand()
                            await self.play_card(p,to_play)
                        except StopIteration:
                            await p.dm("Sorry, that phase has passed!")
                    else:
                        await p.dm("Couldn't understand that!")
                p.redraw()
                if self.game_over:
                    await self.send("The game is over!")
                    for c in self.supplies.keys():
                        c.teardown(self)
                    for vp in self.players:
                        vp.points = sum(c.final_vp(self,vp) for c in vp.all_cards if isinstance(c,VP))
                    await self.show_scoreboard(True)
                    await self.end_points()
                    return
    @property
    def game_over(self):
        if not self.supplies[Province]:
            return True
        elif Colony in self.supplies and not self.supplies[Colony]:
            return True
        return len([s for s in self.supplies.values() if s.empty])>=(3 if len(self.players)<5 else 4)
    def attack_order(self,attacker:DPlayer):
        for delta in range(1,len(self.players)):
            yield self.players[(self.players.index(attacker)+delta)%len(self.players)]

