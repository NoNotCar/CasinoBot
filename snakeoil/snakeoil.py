import dib
import pathlib
import random
import itertools

def load_words(file:pathlib.Path):
    words = set()
    with open(file,"r") as f:
        for w in f.readlines():
            if w:
                words.add(w.strip())
    return list(words)

normal = load_words(pathlib.Path("snakeoil/normal.txt"))
lewd = load_words(pathlib.Path("snakeoil/lewd.txt"))
science = load_words(pathlib.Path("snakeoil/science.txt"))
people = load_words(pathlib.Path("snakeoil/people.txt"))
HAND_SIZE = 6
class SnakeOil(dib.BaseGame):
    name = "snakeoil"
    min_players = 3
    max_players = 20
    async def run(self,*modifiers):
        wset = normal.copy()
        pset = people.copy()
        random.shuffle(pset)
        if "lewd" in modifiers:
            wset.extend(lewd)
        if "science" in modifiers:
            wset.extend(science)
        random.shuffle(self.players)
        rounds = 8 if "long" in modifiers else 3 if "short" in modifiers else 5
        buyer = self.players[0]
        for r in range(rounds):
            role = pset.pop()
            await self.send(f"ROUND {r+1}/{rounds}.\n{buyer.name} is a {role}. Prepare your products!")
            dist = wset.copy()
            random.shuffle(dist)
            sellers = [p for p in self.players if p!=buyer]
            hands = {s:dist[HAND_SIZE*n:HAND_SIZE*(n+1)] for n,s in enumerate(sellers)}
            products = await dib.smart_gather([self.choose_option(s,True,[" ".join(i) for i in itertools.permutations(hands[s],r=2)],
                                                                  f"Make your product! Your hand: {', '.join(hands[s])}",True) for s in sellers],sellers)
            random.shuffle(sellers)
            for s in sellers:
                t = dib.TextTimer(40,self.channel,f"{s.tag}, you've got %s to sell your _wonderful_ product: {products[s]}!")
                await t.run()
            await self.send(f"{buyer.tag}, choose your winner!")
            winner = await self.wait_for_tag(buyer,sellers)
            winner.points+=1
            buyer=winner
        await self.show_scoreboard(True)
        await self.end_points()


