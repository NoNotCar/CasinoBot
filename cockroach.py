import dib
import cards
import random
from collections import defaultdict

BUGS = ["cockroach","worm","rat","frog","fly","scorpion","snake"]
CLAIMS = BUGS+["royal"]
class Bug(cards.BaseCard):
    def __init__(self,bug,royal):
        self.royal = royal
        self.bug = bug
    def matches(self,claim:str):
        if self.bug==claim:
            return True
        return claim=="royal" and self.royal
    @property
    def text(self):
        if self.royal:
            return f"king {self.bug}"
        else:
            return self.bug
    @property
    def short(self):
        return self.text
    @property
    def emoji(self):
        if self.royal:
            return f":crown: :{self.bug}:"
        else:
            return f":{self.bug}:"

bug_deck = [Bug(b,not n) for n in range(8) for b in BUGS]
class BugPlayer(cards.Player):
    card_out = False
    def __init__(self,u,f=False):
        super().__init__(u,f)
        self.collection = defaultdict(list)
    @property
    def status(self):
        if self.collection:
            return ", ".join(f"{bug}: {len(l)}" for bug,l in self.collection.items() if l)
        else:
            return "no cards"
    @property
    def dead(self):
        return self.card_out or any(len(l)>=4 for l in self.collection.values())
    @dead.setter
    def dead(self,new):
        self.card_out=new

class CockroachPoker(cards.CardGame):
    deck=bug_deck
    no_pump = False
    playerclass = BugPlayer
    max_players = 8
    min_players = 3
    name = "cockroach"
    async def run(self,*modifiers):
        random.shuffle(self.players)
        self.deal(8)
        chooser = self.players[0]
        while not any(p.dead for p in self.players):
            if not chooser.hand:
                await self.send(f"{chooser.name} has run out of cards! The game is over!")
                chooser.dead = True
                break
            await self.send("CURRENT STATUS:")
            for p in self.players:
                await self.send(f"{p.name}: {p.status}")
            await chooser.dm("Choose a card to pass to someone!")
            passing = await self.wait_for_play(chooser,prompt=False,private=True)
            passer = chooser
            seen_it = {chooser}
            while True:
                valid_next = [p for p in self.players if p not in seen_it]
                if len(valid_next)==1:
                    passed_to = valid_next[0]
                    await self.send(f"Only one player left, automatically passing to {passed_to.name}.")
                else:
                    await self.send(f"{passer.tag}, choose who to pass the card to!")
                    passed_to = await self.wait_for_tag(passer,valid_next)
                claim = await self.choose_option(passer,False,CLAIMS,f"{passer.name}, what is the passed card?",True)
                await self.send(f"{passer.name} has claimed that the card is a {claim}!")
                if len(valid_next)==1:
                    choice = "take"
                    await self.send(f"{passed_to.name} must take the card!")
                else:
                    choice = await self.choose_option(passed_to,False,["take","pass"],
                                                      f"{passed_to.tag}, do you want to **take** the card or **pass** it on?",True)
                if choice=="take":
                    guess = await self.yn_option(passed_to,False,"Are they telling the truth?")
                    if guess==passing.matches(claim):
                        await self.send(f"CORRECT! {passer.name} takes the card!")
                        await self.take_card(passer,passing)
                        chooser=passer
                    else:
                        await self.send("WRONG! You take the card!")
                        await self.take_card(passed_to,passing)
                        chooser=passed_to
                    break
                else:
                    passer=passed_to
                    await passer.dm(f"You peek at the card and see a {passing.text}!")
                    seen_it.add(passer)
        await self.end_game([p for p in self.players if not p.dead])
    async def take_card(self,p:BugPlayer,card:Bug):
        if card.royal:
            await self.send(f"The card was {card.text}, so {p.name} also takes a penalty card!")
            penalty = Bug(random.choice(BUGS),False)
            p.collection[penalty.bug].append(penalty)
        p.collection[card.bug].append(card)

