import asyncio
from discord.ext import commands
from economy import get_user
from functools import total_ordering
import random
import dib
from collections import defaultdict
task=asyncio.create_task
suits=["clubs","diamonds","hearts","spades"]
suit_emoji=[":clubs:",":diamonds:",":hearts:",":spades:"]
ranks=[str(n) for n in range(2,11)]+["jack","queen","king","ace"]
rank_emoji=[":%s:" % r for r in ["two","three","four","five","six","seven","eight","nine","keycap_ten","regional_indicator_j","regional_indicator_q","regional_indicator_k","regional_indicator_a"]]
def shuffled(l):
    l=l[:]
    random.shuffle(l)
    return l
@total_ordering
class Card(object):
    def __init__(self,rank,suit):
        self.rank=rank
        self.suit=suit
    def __eq__(self, other):
        return isinstance(other,Card) and (self.suit,self.rank)==(other.suit,other.rank)
    def __lt__(self, other):
        return ranks.index(self.rank)<ranks.index(other.rank) or ((self.rank==other.rank) and suits.index(self.suit)<suits.index(other.suit))
    def __repr__(self):
        return "Card: "+self.text
    @property
    def text(self):
        return "%s of %s" % (self.rank,self.suit)
    @property
    def emoji(self):
        return rank_emoji[ranks.index(self.rank)]+suit_emoji[suits.index(self.suit)]
deck_52 =sorted([Card(r, s) for r in ranks for s in suits])
class Player(dib.BasePlayer):
    sorted=True
    score=0
    handmsg=None
    async def set_hand(self,hand):
        self.hand=sorted(hand,key=lambda c:(c.suit,ranks.index(c.rank))) if self.sorted else list(hand)
        await task(self.update())
    async def remove_card(self,card):
        self.hand.remove(card)
        await task(self.update())
    async def add_card(self,card):
        self.hand.append(card)
        if self.sorted:
            self.hand=sorted(self.hand,key=lambda c:(c.suit,ranks.index(c.rank)))
        await task(self.update())
    async def update(self):
        if self.handmsg:
            await task(self.handmsg.edit(content=self.msg))
        else:
            self.handmsg = await self.user.dm(self.msg)
    @property
    def msg(self):
        return "YOUR HAND: "+", ".join(c.emoji for c in self.hand)
class CardGame(dib.BaseGame):
    min_players=3
    max_players=6
    playing=False
    deck=deck_52
    playerclass = Player
    async def run(self,*modifiers):
        self.playing=True
    async def deal(self,n=-1):
        if n==-1:
            n=len(self.deck)//len(self.players)
            deck=self.deck[len(self.deck)-n*len(self.players):]
        else:
            deck = self.deck[:]
        random.shuffle(deck)
        for i,p in enumerate(self.players):
            await p.set_hand(deck[i*n:i*n+n])
    async def wait_for_play(self,player:Player,f_valid=lambda c:True,prompt=True):
        card = await self.smart_options(player,False,[c for c in player.hand if f_valid(c)],lambda c:c.text,("%s's turn:" % player.name if prompt else ""),True)
        await player.remove_card(card)
        return card
class Hearts(CardGame):
    hearts_broken=False
    target=50
    name="hearts"
    async def run(self,*modifiers):
        try:
            self.target=int(modifiers[0])
        except IndexError:
            pass
        except ValueError:
            pass
        await super().run()
        random.shuffle(self.players)
        turn=0
        while not any(p.score>=self.target for p in self.players):
            await self.deal()
            winnings=defaultdict(list)
            self.hearts_broken=False
            for _ in range(len(self.players[0].hand)):
                await self.channel.send("%s leads.%s" % (self.players[turn].name,"" if self.hearts_broken else " Hearts are currently unbroken."))
                stack=[await self.wait_for_play(self.players[turn],lambda c: self.hearts_broken or all(c.suit=="hearts" for c in self.players[turn].hand) or c.suit!="hearts",False)]
                suit=stack[0].suit
                for _ in range(len(self.players)-1):
                    turn+=1
                    turn%=len(self.players)
                    await self.channel.send("%s's turn. Played: %s" % (self.players[turn].name,", ".join(c.emoji for c in stack)))
                    stack.append(await self.wait_for_play(self.players[turn],lambda c: not any(h.suit==suit for h in self.players[turn].hand) or c.suit==suit,False))
                turn=(stack.index(max(c for c in stack if c.suit==suit))+(turn-len(self.players)+1))%len(self.players)
                if any(c.suit=="hearts" for c in stack):
                    self.hearts_broken=True
                await self.channel.send("%s won the trick!" % self.players[turn].name)
                winnings[self.players[turn]].extend(stack)
            winnings={p:sum(1 if c.suit=="hearts" else 13 if c.text=="queen of spades" else 0 for c in w) for p,w in winnings.items()}
            if 26 in list(winnings.values()):
                moonshooter=next(p for p in winnings if winnings[p]==26)
                await self.channel.send("%s successfully shot the moon! They gain an extra 5c!" % moonshooter.name)
                moonshooter.user.update_balance(5)
                for p in self.players:
                    if p is not moonshooter:
                        p.score+=26
            else:
                for p,w in winnings.items():
                    p.score+=w
            await self.channel.send("CURRENT SCORES:\n"+"\n".join("%s: %s" % (p.name,p.score) for p in self.players))
        winners=[p for p in self.players if p.score==min(p.score for p in self.players)]
        await self.channel.send("The game is over. %s won and %s 10c!" % (", ".join(w.name for w in winners),"gets" if len(winners)==1 else "get"))
        for w in winners:
            w.user.update_balance(10)
        await self.end_game(winners)
class OhHell(CardGame):
    name="ohhell"
    CORRECT=10
    min_players = 2
    async def run(self,*modifiers):
        random.shuffle(self.players)
        max_round = min(10,52//len(self.players))
        for r in range(1,max_round+1):
            trumps = random.choice(suits)
            await self.deal(r)
            await self.send("ROUND %s/%s. Trumps are %s." % (r,max_round,trumps))
            bets={}
            dealer = self.players[-1]
            for p in self.players[:-1]:
                bets[p]=await self.choose_number(p,False,0,r,"%s, bet how many tricks you will win." % p.name)
            while True:
                bets[dealer] = await self.choose_number(dealer, False, 0, r, "%s, bet how many tricks you will win." % dealer.name)
                if sum(bets.values())!=r:
                    break
                await self.send("The sum of bets cannot be equal to the total number of tricks, bet again!")
            wins={p:0 for p in self.players}
            turn=0
            for _ in range(r):
                await self.channel.send("%s leads." % self.players[turn].name)
                stack=[await self.wait_for_play(self.players[turn])]
                suit=stack[0].suit
                for _ in range(len(self.players)-1):
                    turn+=1
                    turn%=len(self.players)
                    await self.channel.send("%s's turn. Played: %s" % (self.players[turn].name,", ".join(c.emoji for c in stack)))
                    stack.append(await self.wait_for_play(self.players[turn],lambda c: not any(h.suit==suit for h in self.players[turn].hand) or c.suit==suit,False))
                winning_card = max(c for c in stack if c.suit==trumps) if any(c.suit==trumps for c in stack) else max(c for c in stack if c.suit==suit)
                turn=(stack.index(winning_card)+(turn-len(self.players)+1))%len(self.players)
                await self.channel.send("%s won the trick!" % self.players[turn].name)
                wins[self.players[turn]]+=1
            for p in self.players:
                if wins[p]==bets[p]:
                    await self.send("%s made their bid and wins %s points!" % (p.name,wins[p]+self.CORRECT))
                    p.points+=wins[p]+self.CORRECT
                else:
                    await self.send("%s did not make their bid and gets %s points." % (p.name, wins[p]))
                    p.points += wins[p]
            await self.show_scoreboard()
            dib.revolve(self.players)
        await self.end_points()