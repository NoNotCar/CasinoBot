import asyncio
from discord.ext import commands
from economy import get_user
from functools import total_ordering
import random
import dib
from collections import defaultdict
import typing
task=asyncio.create_task
suits=["mice","birds","crabs","wolves"]
suit_emoji=[":mouse:",":bird:",":crab:",":wolf:"]
ranks=[str(n) for n in range(2,11)]+["jack","queen","king","ace"]
rank_emoji=[":%s:" % r for r in ["two","three","four","five","six","seven","eight","nine","keycap_ten","regional_indicator_j","regional_indicator_q","regional_indicator_k","regional_indicator_a"]]
def shuffled(l):
    l=l[:]
    random.shuffle(l)
    return l
class BaseCard(object):
    @property
    def text(self):
        return "card"
    @property
    def short(self):
        return "C"
    @property
    def emoji(self):
        return ":white_large_square:"
    @property
    def hand_sort(self):
        return 0
    def __repr__(self):
        return self.text
@total_ordering
class Card(BaseCard):
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
    def short(self):
        return (self.rank[0].upper() if self.rank!="10" else self.rank)+self.suit[0].upper()
    @property
    def emoji(self):
        return rank_emoji[ranks.index(self.rank)]+suit_emoji[suits.index(self.suit)]

    @property
    def hand_sort(self):
        return suits.index(self.suit), ranks.index(self.rank)
@total_ordering
class DalmutiCard(BaseCard):
    emojis=[":crown:",":cross:",":military_helmet:",":face_with_monocle:",":woman_with_headscarf:",":guard:",":thread:",
            ":house:",":cook:",":sheep:",":rock:",":poop:",":black_joker:"]
    names=["dalmuti","archbishop","earl marshall","baroness","abbess","knight","seamstress","mason","cook",
           "shepherdess","stonecutter","peasant","joker"]
    def __init__(self,rank):
        self.rank=rank
    def __eq__(self, other):
        return self.rank==other.rank
    def __lt__(self, other):
        return self.rank<other.rank
    @property
    def text(self):
        return self.names[self.rank-1]
    @property
    def emoji(self):
        return self.emojis[self.rank-1]
    @property
    def short(self):
        return str(self.rank) if self.rank!=13 else "J"
    @property
    def hand_sort(self):
        return self.rank
deck_52 =sorted([Card(r, s) for r in ranks for s in suits])
deck_dalmuti = sorted([DalmutiCard(r) for r in range(1,13) for _ in range(r)]+[DalmutiCard(13)]*2)
class Player(dib.BasePlayer):
    sorted=True
    score=0
    handmsg=None
    def set_hand(self,hand):
        self.hand=sorted(hand,key=lambda c:c.hand_sort) if self.sorted else list(hand)
        task(self.update(True))
    def remove_card(self,card):
        self.hand.remove(card)
        task(self.update())
    def add_card(self,card):
        self.hand.append(card)
        if self.sorted:
            self.hand=sorted(self.hand,key=lambda c:(c.suit,ranks.index(c.rank)))
        task(self.update())
    async def update(self,resend=False):
        if self.handmsg and not resend:
            task(self.handmsg.edit(content=self.msg))
        else:
            self.handmsg = await self.user.dm(self.msg)
    def could_play(self,cards:typing.List[BaseCard]):
        test_hand = self.hand.copy()
        for c in cards:
            if c in test_hand:
                test_hand.remove(c)
            else:
                return False
        return True
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
    def deal(self,n=-1):
        if n==-1:
            n=len(self.deck)//len(self.players)
            deck=self.deck[len(self.deck)-n*len(self.players):]
        else:
            deck = self.deck[:]
        random.shuffle(deck)
        for i,p in enumerate(self.players):
            p.set_hand(deck[i*n:i*n+n])
    def deal_all(self):
        deck = self.deck[:]
        random.shuffle(deck)
        for i,p in enumerate(self.players):
            p.set_hand(deck[i::len(self.players)])
    async def wait_for_play(self,player:Player,f_valid=lambda c:True,prompt=True):
        card = await self.smart_options(player,False,[c for c in player.hand if f_valid(c)],lambda c:(c.text,c.short),("%s's turn:" % player.name if prompt else ""),True)
        player.remove_card(card)
        return card
    async def wait_for_multiplay(self,player:Player,message="Play some cards",min_cards = 1,max_cards = 1,f_valid=lambda c: True,private=False):
        send = player.dm if private else self.send
        while True:
            text = await self.wait_for_text(player,message,private,faked=", ".join(c.short for c in random.sample(player.hand,min_cards)))
            if text.lower()=="pass" and min_cards==0:
                return []
            hand=[]
            for cs in text.split(","):
                cs=cs.strip().lower()
                for c in player.hand:
                    if c.text.lower()==cs or c.short.lower()==cs:
                        if f_valid(c):
                            hand.append(c)
                            break
                else:
                    await send('Card "%s" is invalid, try again!' % cs)
                    break
            else:
                if min_cards<=len(hand)<=max_cards:
                    if player.could_play(hand):
                        return hand
                    else:
                        await send("You don't have that many copies!")
                else:
                    await send("Incorrect number of cards!")
class Hearts(CardGame):
    hearts_broken=False
    target=50
    name=suits[2]
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
        passing = 0
        while not any(p.score>=self.target for p in self.players):
            self.deal()
            winnings=defaultdict(list)
            self.hearts_broken=False
            if passing:
                await self.send("IT'S PASSING TIME!")
                passed = await dib.gather([self.wait_for_multiplay(p,"Choose 3 cards to give to an opponent!",3,3) for p in self.players])
                for i,p in enumerate(self.players):
                    for c in passed[i]:
                        p.hand.remove(c)
                        self.players[(i+passing)%len(self.players)].hand.append(c)
                for p in self.players:
                    await p.update()
            for _ in range(len(self.players[0].hand)):
                if len(self.players[0].hand)==1:
                    stack = [self.players[(turn+i)%len(self.players)].hand[0] for i,_ in enumerate(self.players)]
                    await self.send("Last round! Autoplayed: %s" % ", ".join(c.emoji for c in stack))
                    suit = stack[0].suit
                    turn -= 1
                    turn %= len(self.players) - 1
                else:
                    await self.channel.send("%s leads.%s" % (self.players[turn].tag,"" if self.hearts_broken else " %s are currently unbroken." % suits[2].capitalize()))
                    stack=[await self.wait_for_play(self.players[turn],lambda c: self.hearts_broken or all(c.suit==suits[2] for c in self.players[turn].hand) or c.suit!=suits[2],False)]
                    suit=stack[0].suit
                    for _ in range(len(self.players)-1):
                        turn+=1
                        turn%=len(self.players)
                        await self.channel.send("%s's turn. Played: %s" % (self.players[turn].tag,", ".join(c.emoji for c in stack)))
                        stack.append(await self.wait_for_play(self.players[turn],lambda c: not any(h.suit==suit for h in self.players[turn].hand) or c.suit==suit,False))
                turn=(stack.index(max(c for c in stack if c.suit==suit))+(turn-len(self.players)+1))%len(self.players)
                if any(c.suit==suits[2] for c in stack):
                    self.hearts_broken=True
                await self.channel.send("%s won the trick!" % self.players[turn].name)
                winnings[self.players[turn]].extend(stack)
            winnings={p:sum(1 if c.suit==suits[2] else 13 if c.text=="queen of %s" % suits[3] else 0 for c in w) for p,w in winnings.items()}
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
            passing=(passing+2)%3-1
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
            self.deal(r)
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
                if len(self.players[0].hand)==1:
                    stack = [self.players[(turn+i)%len(self.players)].hand[0] for i,_ in enumerate(self.players)]
                    await self.send("Last round! Autoplayed: %s" % ", ".join(c.emoji for c in stack))
                    suit = stack[0].suit
                    turn-=1
                    turn%=len(self.players)-1
                else:
                    await self.channel.send("%s leads." % self.players[turn].name)
                    stack=[await self.wait_for_play(self.players[turn])]
                    suit=stack[0].suit
                    for _ in range(len(self.players)-1):
                        turn+=1
                        turn%=len(self.players)
                        await self.channel.send("%s's turn. Played: %s" % (self.players[turn].tag,", ".join(c.emoji for c in stack)))
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
class GreatDalmuti(CardGame):
    deck=deck_dalmuti
    info = {"dalmuti":"CARDS:\n"+"\n".join("%s: %s %s" % (c.short,c.text,c.emoji) for c in [DalmutiCard(r) for r in range(1,14)])}
    name="dalmuti"
    max_players = 9
    min_players = 5
    lengths={"short":4,"standard":6,"long":8,"extreme":12}
    def valid_play(self,player:Player,text:str,repeats=False):
        split=text.split()
        if not split:
            return []
        first=split[0]
        played=[]
        test_hand=player.hand.copy()
        for s in split:
            if s==first or s=="J":
                for t in test_hand:
                    if t.short==s or repeats:
                        test_hand.remove(t)
                        played.append(t)
                        break
                else:
                    return []
        return played
    async def run(self,*modifiers):
        if modifiers and modifiers[0] in self.lengths:
            rounds=self.lengths[modifiers[0]]
        else:
            await self.send("No game length specified, using default of %s rounds!" % self.lengths["standard"])
            rounds=self.lengths["standard"]
        random.shuffle(self.players)
        for n in range(rounds):
            await self.send("ROUND %s/%s\nCURRENT ORDER: %s" % (n+1,rounds,"|".join(p.name for p in self.players)))
            great_dalmuti=self.players[0]
            lesser_dalmuti=self.players[1]
            lesser_peon=self.players[-2]
            greater_peon=self.players[-1]
            random.shuffle(self.deck)
            self.deal_all()
            for p in self.players:
                if len([c for c in p.hand if c.short=="J"])==2:
                    answer = await self.choose_option(p,True,["yes","no"],"You have 2 Jokers! Start a revolution?")
                    if answer=="yes":
                        await self.send("%s has started a %s!" % (p.name,"revolution" if p!=greater_peon else "greater revolution"))
                        if p==greater_peon:
                            self.players.reverse()
                        break
            else:
                if n:
                    await self.send("Waiting for the dalmutis to choose cards to send!")
                    gifts=await dib.gather([self.wait_for_text(d,"Choose %s cards to give to the relevant peon!" % (2-n),True,
                                                         lambda t, d=d, on=n:len(self.valid_play(d,t,True))==2-on,
                                      faked=" ".join(c.short for c in random.sample(d.hand,2-n)))
                                      for n,d in enumerate([great_dalmuti,lesser_dalmuti])])
                    gifts=[self.valid_play(d,gifts[n]) for n,d in enumerate([great_dalmuti,lesser_dalmuti])]
                    for n,g in enumerate(gifts):
                        for c in g:
                            (great_dalmuti,lesser_dalmuti)[n].hand.remove(c)
                    taxes=[[],[]]
                    for n,peon in enumerate((greater_peon,lesser_peon)):
                        for _ in range(2-n):
                            tax = min(peon.hand)
                            taxes[n].append(tax)
                            peon.hand.remove(tax)
                        peon.hand.extend(gifts[n])
                    for n,d in enumerate((great_dalmuti,lesser_dalmuti)):
                        d.hand.extend(taxes[n])
                    for p in (great_dalmuti,lesser_dalmuti,lesser_peon,greater_peon):
                        await p.update()
            turn=0
            passes=0
            last_played=[]
            last_pturn=0
            next_order=[]
            while len(next_order)<len(self.players)-1:
                playing=self.players[turn]
                if playing.hand:
                    if last_played:
                        await self.send("Last played: %s. %s, choose cards to play or pass!" % (" ".join(c.emoji for c in last_played),playing.tag))
                    else:
                        await self.send("%s, choose cards to lead with!" % playing.tag)
                    while True:
                        i=await self.wait_for_text(playing,"",False,lambda t,p=playing:t=="pass" or self.valid_play(p,t),
                            faked=random.choice([c.short for c in playing.hand]) if not last_played or (len(last_played)==1 and random.randint(0,1)) else "pass")
                        if not last_played and i=="pass":
                            await self.send("You can't pass when leading!")
                        elif last_played and i!="pass" and len(i.split())!=len(last_played):
                            await self.send("Incorrect number of cards!")
                        elif last_played and i!="pass" and self.valid_play(playing,i)[0]>=last_played[0]:
                            await self.send("You have to _beat_ the previous player!")
                        else:
                            if i=="pass":
                                passes+=1
                                if passes==len(self.players)-1:
                                    await self.send("Everyone passed!")
                                    turn=last_pturn
                                    last_played=[]
                                    passes=0
                                else:
                                    turn+=1
                            else:
                                last_played=self.valid_play(playing,i)
                                last_pturn=turn
                                for l in last_played:
                                    playing.remove_card(l)
                                if not playing.hand:
                                    await self.send("%s is out of cards!" % playing.name)
                                    next_order.append(playing)
                                turn+=1
                                passes=0
                            break
                else:
                    passes += 1
                    if passes == len(self.players) - 1:
                        await self.send("Everyone passed!")
                        turn = last_pturn
                        last_played=[]
                        passes=0
                    else:
                        turn += 1
                turn%=len(self.players)
            self.players=next_order+[p for p in self.players if p not in next_order]
        for n,p in enumerate(self.players):
            p.points=len(self.players)-n
        await self.end_points()



