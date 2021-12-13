from __future__ import annotations
import cards
import dib
from functools import total_ordering
import typing
import random
import asyncio


colours = ["red","orange","yellow","green","blue","purple","brown"]
@total_ordering
class Card7(cards.BaseCard):
    def __init__(self,rank:int,colour:int):
        self.rank=rank
        self.colour=colour
    def __eq__(self, other):
        return isinstance(other,Card7) and (self.colour,self.rank)==(other.colour,other.rank)
    def __lt__(self, other:Card7):
        return self.rank<other.rank or ((self.rank==other.rank) and self.colour>other.colour)
    def __repr__(self):
        return "Card: "+self.text
    def __hash__(self):
        return hash((self.rank,self.colour))
    def copied(self):
        return self.__class__(self.rank,self.colour)
    @property
    def rule(self)->Rule:
        return [Red,Orange,Yellow,Green,Blue,Purple,Brown][self.colour]()
    @property
    def text(self):
        return f"{colours[self.colour].capitalize()} {self.rank+1}"
    @property
    def short(self):
        return self.text
    @property
    def emoji(self):
        return f":{colours[self.colour]}_square:{dib.to_emoji(self.rank+1)}"

    @property
    def hand_sort(self):
        return self.colour, self.rank
class Rule(object):
    desc = "idk"
    def valid_set(self, palette: typing.List[Card7]) -> typing.Set[Card7]:
        return set()
class Red(Rule):
    desc = "Highest card wins"
    def valid_set(self, palette: typing.List[Card7]) -> typing.Set[Card7]:
        return {max(palette)}
class Orange(Rule):
    desc = "Most of one number wins"
    def valid_set(self, palette: typing.List[Card7]) -> typing.Set[Card7]:
        best_set = set()
        for c in palette:
            challenger = {card for card in palette if card.rank == c.rank}
            if len(challenger)>len(best_set):
                best_set=challenger
        return best_set
class Yellow(Rule):
    desc = "Most of one colour wins"
    def valid_set(self, palette: typing.List[Card7]) -> typing.Set[Card7]:
        best_set = set()
        for c in palette:
            challenger = {card for card in palette if card.colour == c.colour}
            if len(challenger)>len(best_set):
                best_set=challenger
        return best_set
class Green(Rule):
    desc = "Most even cards wins"
    def valid_set(self, palette: typing.List[Card7]) -> typing.Set[Card7]:
        return {c for c in palette if c.rank % 2}
class Blue(Rule):
    desc = "Most different colours wins"
    def valid_set(self, palette: typing.List[Card7]) -> typing.Set[Card7]:
        s=set()
        for n,_ in enumerate(colours):
            if matching:= [c for c in palette if c.colour == n]:
                s.add(max(matching))
        return s
class Purple(Rule):
    desc = "Most cards in a row wins"
    def valid_set(self, palette: typing.List[Card7]) -> typing.Set[Card7]:
        best_set = set()
        for rs in range(6,-1,-1):
            if matching:=[c for c in palette if c.rank == rs]:
                row = {max(matching)}
                for nxt in range(rs-1,-1,-1):
                    if om := [c for c in palette if c.rank == rs]:
                        row.add(max(om))
                    else:
                        break
                if len(row)>len(best_set):
                    best_set=row
        return best_set
class Brown(Rule):
    desc = "Most cards below 4 wins"
    def valid_set(self, palette: typing.List[Card7]) -> typing.Set[Card7]:
        return {c for c in palette if c.rank < 3}
r7deck = [Card7(r,c) for r in range(7) for c in range(7)]
rules = [Card7(1,c).rule for c in range(7)]
class Red7Player(cards.Player):
    def __init__(self,u,f=False):
        super().__init__(u,f)
        self.palette = []
    @property
    def alive(self):
        return not self.points
class Red7(cards.CardGame):
    name = "red7"
    min_players = 2
    max_players = 6
    deck = r7deck
    playerclass = Red7Player
    no_pump = False
    info = {colours[n]:f"{colours[n].capitalize()}: {rules[n].desc}" for n in range(7)}
    def is_winning(self,player:Red7Player,rule:Rule):
        winning_set = rule.valid_set(player.palette)
        if not winning_set:
            return False
        for p in self.players:
            if p!=player and p.alive:
                if challenge_set:=rule.valid_set(p.palette):
                    if len(challenge_set)>len(winning_set):
                        return False
                    elif len(challenge_set)==len(winning_set) and max(challenge_set)>max(winning_set):
                        return False
        return True
    async def run(self,*modifiers):
        random.shuffle(self.players)
        rule = Red()
        self.deal(8)
        await asyncio.sleep(3)
        for p in self.players:
            first = p.hand[0]
            p.palette.append(first)
            p.remove_card(first)
        winning = next(p for p in self.players if self.is_winning(p,rule))
        turn = self.players.index(winning)
        cnp = -len(self.players)
        while len([p for p in self.players if p.alive])>1:
            while True:
                turn+=1
                turn%=len(self.players)
                if self.players[turn].alive:
                    break
            current_player = self.players[turn]
            await self.send(f"{current_player.tag}'s turn! Current rule: {rule.desc}. Current palettes:")
            for p in self.players:
                if p.alive:
                    await self.send(p.name+":"+",".join(c.emoji for c in p.palette))
            current_player.palette.extend(await self.wait_for_multiplay(current_player,"Choose a card to add to your palette, or pass",0,1))
            new_rule=None
            if canvas:=await self.wait_for_multiplay(current_player,"Choose a card to change the rule, or pass",0,1):
                new_rule = canvas[0].rule
            if self.is_winning(current_player,new_rule or rule):
                if new_rule:
                    rule=new_rule
                await self.send("Hooray! You're winning!")
            else:
                await self.send("Oh no! You're not winning! TOO BAD!")
                current_player.points = cnp
                cnp+=1
        await self.end_points()



