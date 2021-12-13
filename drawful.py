import dib
import random
import asyncio
from collections import defaultdict

class DrawfulRound(object):
    prompt=None
    pic=None
    def __init__(self,prompter,drawer):
        self.prompter=prompter
        self.drawer=drawer
        self.guesses={}
    def get_others(self,ps):
        return [p for p in ps if p not in [self.prompter,self.drawer]]
    async def submit_phase(self,game):
        self.prompt=await game.wait_for_text(self.prompter,"Submit your prompt:", confirmation="%s has submitted their prompt!")
        await self.prompter.dm("Thanks!")
    async def draw_phase(self,game):
        self.pic=await game.wait_for_picture(self.drawer,"Draw this: %s" % self.prompt)
        await self.drawer.dm("Thanks!")
async def p_guess_phase(p:dib.BasePlayer,game:dib.BaseGame,rounds):
    for r in rounds:
        if p!=r.prompter and p!=r.drawer:
            r.guesses[p]=await game.wait_for_text(p, "Describe this: %s" % r.pic)
    await game.send("%s has finished describing!" % p.name)
class Drawful(dib.BaseGame):
    name="drawful"
    min_players = 3
    max_players = 12
    SMART_POINTS=5
    GUESS_POINTS=2
    INTERCEPT_POINTS=2
    GOOD_DRAWING_POINTS=1
    async def run(self,*modifiers):
        random.shuffle(self.players)
        rounds=[DrawfulRound(p,self.players[n-1]) for n,p in enumerate(self.players)]
        random.shuffle(rounds)
        await dib.gather([r.submit_phase(self) for r in rounds])
        await dib.gather([r.draw_phase(self) for r in rounds])
        await dib.gather([p_guess_phase(p,self,rounds) for p in self.players])
        await self.channel.send("It's voting time!")
        for r in rounds:
            smart_people=[]
            other_prompts=defaultdict(list)
            other_prompts[r.prompt].append(r.prompter)
            for p,guess in r.guesses.items():
                if guess.lower()==r.prompt.lower():
                    smart_people.append(p)
                else:
                    other_prompts[guess].append(p)
            if len(other_prompts)>1:
                await self.channel.send("%s drew this: %s\nWhat was the original prompt?" % (r.drawer.name,r.pic))
                if smart_people:
                    await self.channel.send("%s guessed the prompt correctly and get %spts!" % (dib.smart_list([p.name for p in smart_people]),self.SMART_POINTS))
                    for p in smart_people:
                        p.points+=self.SMART_POINTS
                opl=list(other_prompts.keys())
                random.shuffle(opl)
                await self.channel.send("\n".join("%s: %s" % (n+1,prompt) for n,prompt in enumerate(opl)))
                guessers=[p for p in r.get_others(self.players) if p not in smart_people]
                guesses=await dib.smart_gather([self.choose_number(g,True,1,len(opl),"Guess which prompt is correct!") for g in guessers],guessers)
                correct=opl.index(r.prompt)+1
                for p,g in guesses.items():
                    if g==correct:
                        await self.channel.send("%s guessed the correct prompt! They get %spts and the drawer gets %spt." % (p.name,self.GUESS_POINTS,self.GOOD_DRAWING_POINTS))
                        p.points+=self.GUESS_POINTS
                        r.drawer.points+=self.GOOD_DRAWING_POINTS
                    else:
                        interceptors=other_prompts[opl[g-1]]
                        if p in interceptors:
                            await self.channel.send("%s guessed their own prompt! NO POINTS!" % p.name)
                        else:
                            await self.channel.send("%s guessed %s's prompt! They get %spts!" % (p.name,dib.smart_list([pp.name for pp in interceptors] ),self.INTERCEPT_POINTS))
                            for pp in interceptors:
                                pp.points+=self.INTERCEPT_POINTS
            else:
                await self.channel.send("Everybody guessed the prompt correctly! Are you all psychic???")
                for p in r.get_others(self.players):
                    p.points+=self.SMART_POINTS
        await self.show_scoreboard(True)
        await self.end_points()


