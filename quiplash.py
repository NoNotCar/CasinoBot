import dib
import random
from collections import defaultdict

class Quip(object):
    prompt=None
    def __init__(self,prompter,finishers):
        self.prompter=prompter
        self.finishers=finishers
        self.finishes={}
    def get_others(self,ps):
        return [p for p in ps if p not in self.finishers]
    async def submit_phase(self,game):
        self.prompt=await game.wait_for_text(self.prompter,"Submit your prompt:",confirmation="%s has submitted their prompt!")
        await self.prompter.dm("Thanks!")
async def p_finish_phase(p:dib.BasePlayer,game:dib.BaseGame,rounds):
    for r in rounds:
        if p in r.finishers:
            r.finishes[p]=await game.wait_for_text(p, "Your prompt: %s" % r.prompt)
    await game.send("%s has finished their submissions!" % p.name)
class Quiplash(dib.BaseGame):
    name="quiplash"
    min_players = 5
    max_players = 20
    async def run(self,*modifiers):
        random.shuffle(self.players)
        w=self.players+self.players
        quips=[Quip(p,w[n+1:n+1+len(self.players)//2]) for n,p in enumerate(self.players)]
        await dib.gather([r.submit_phase(self) for r in quips])
        await dib.gather([p_finish_phase(p,self,quips) for p in self.players])
        await self.channel.send("It's voting time!")
        random.shuffle(quips)
        for r in quips:
            finishes=defaultdict(list)
            for p,fin in r.finishes.items():
                finishes[fin].append(p)
            if len(finishes)>1:
                await self.channel.send("%s gave this prompt: %s" % (r.prompter.name,r.prompt))
                fl=list(finishes.keys())
                random.shuffle(fl)
                await self.channel.send("\n".join("%s: %s" % (n+1,prompt) for n,prompt in enumerate(fl)))
                voters=r.get_others(self.players)
                guesses=await dib.smart_gather([self.choose_number(g,True,1,len(fl),"Vote for your favourite ending!") for g in voters],voters)
                for n,f in enumerate(fl):
                    if voted:= [v for v in voters if guesses[v]==n+1]:
                        await self.send("%s voted for %s's \"%s\" - %s points!" % (dib.smart_list([v.name for v in voted]),dib.smart_list([p.name for p in finishes[f]]),f,len(voted)))
                        for p in finishes[f]:
                            p.points+=len(voted)
            else:
                await self.channel.send("Everybody put the same ending! Are you all psychic??? NO POINTS!")
        await self.show_scoreboard(True)
        await self.end_points()
