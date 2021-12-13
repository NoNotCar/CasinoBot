import dib
import pimg
import pathlib
import typing
from vector import V2
from PIL import ImageFont
import random

cards = []
WIDTH = 300
HEIGHT = 485
EXTRA = 64
BACK = (200,)*3
bigbas = ImageFont.truetype("fonts/bebas.ttf",64)
for cp in pathlib.Path.cwd().glob("dixit/cards/*.png"):
    cards.append(pimg.load(cp))

def render_card_array(ca:typing.List[pimg.PImg]):
    img = pimg.PImg.filled(V2(WIDTH*len(ca),HEIGHT+EXTRA),BACK)
    for n,c in enumerate(ca):
        img.blit(c,V2(WIDTH*n,EXTRA))
        img.write(str(n+1),bigbas,V2(WIDTH*n+WIDTH/2,EXTRA/2))
    return img

HAND_SIZE = 6
class Dixit(dib.BaseGame):
    max_players = len(cards)//HAND_SIZE
    min_players = 3
    name = "dixit"
    async def run(self,*modifiers):
        deck = cards[:]
        discard = []
        hands = {p:[] for p in self.players}
        random.shuffle(self.players)
        random.shuffle(deck)
        while not any(p.points>=30 for p in self.players):
            for storyteller in self.players:
                await self.send(f"{storyteller.name} is the storyteller for this round.")
                for p in self.players:
                    while len(hands[p])<HAND_SIZE:
                        if not deck:
                            deck.extend(discard)
                            discard.clear()
                        assert deck, "OH NO THE DECK IS EMPTIES"
                        hands[p].append(deck.pop())
                    if not p.fake:
                        await render_card_array(hands[p]).dm_send(p)
                guessers = [p for p in self.players if p!=storyteller]
                stcard = hands[storyteller].pop(await self.choose_number(storyteller,True,1,6,"Choose a card to describe!")-1)
                story = await self.wait_for_text(storyteller,"Describe the card!")
                await self.send(f"{storyteller.name}'s Story: {story}\nSubmit your cards!")
                gcards = await dib.smart_gather([self.choose_number(g,True,1,6,"Choose a card to submit!") for g in guessers],guessers)
                gcards = {g:hands[g].pop(n-1) for g,n in gcards.items()}
                ownerships = {c:g for g,c in gcards.items()}
                ownerships[stcard]=storyteller
                choices = list(ownerships.keys())
                random.shuffle(choices)
                await render_card_array(choices).send(self.channel)
                await self.send("Guessers, guess which card is correct!")
                guesses = await dib.smart_gather([self.choose_number(g,True,1,len(choices),"Guess which card is correct!") for g in guessers],guessers)
                guesses = {g:choices[c-1] for g,c in guesses.items()}
                if all(choice==stcard for choice in guesses.values()):
                    await self.send(f"Everyone got it right! {storyteller.name} gets no points!")
                    for g in guessers:
                        g.points+=2
                else:
                    messages = [f"The correct card was card {choices.index(stcard)+1}"]
                    for g,c in guesses.items():
                        if c==stcard:
                            messages.append(f"{g.name} got it right, and gets 3 points!")
                            g.points+=3
                        elif g == ownerships[c]:
                            messages.append(f"{g.name} chose their own card, and loses 1 point for their idiocy!")
                            g.points-=1
                        else:
                            messages.append(f"{g.name} chose {ownerships[c].name}'s card, they get 1 point!")
                            ownerships[c].points+=1
                    if any(choice==stcard for choice in guesses.values()):
                        messages.append(f"At least one person got it right, so {storyteller.name} gets 3 points!")
                        storyteller.points+=3
                    else:
                        messages.append(f"Nobody got it right, so all guessers get 2 points!")
                        for g in guessers:
                            g.points += 2
                    await self.long_send(messages)
                await self.show_scoreboard(False)
                discard.extend(choices)
        await self.send("Someone has 30+ points, so the game has ended!")
        await self.end_points()




