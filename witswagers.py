from __future__ import annotations
import dib
import random
from collections import defaultdict
CORRECT=2
def is_int(s:str):
    try:
        int(s)
        return True
    except ValueError:
        return False
class Round(object):
    question=None
    answer=None
    def __init__(self,qm):
        self.qm=qm
        self.answers=dib.bidict({})
        self.bets=defaultdict(dict)
    async def question_phase(self,game:WitsAndWagers):
        self.question=await game.wait_for_text(self.qm,"Submit a question with an integer answer, without the answer :P")
        self.answer=int(await game.wait_for_text(self.qm,"Submit the answer now",True,is_int))
    async def answer_phase(self,game:WitsAndWagers):
        answerers=[p for p in game.players if p is not self.qm]
        self.answers=await dib.smart_gather([game.wait_for_text(p,"Submit your answer!",True,is_int,"%s has submitted their guess") for p in answerers],answerers)
        self.answers=dib.bidict({p:int(a) for p,a in self.answers.items()})
    async def betting_phase(self,game:WitsAndWagers):
        unique_answers=list(self.answers.inverse.keys())
        unique_answers.sort()
        if len(unique_answers)%2:
            bet_rows=[(abs(len(unique_answers)//2-n)+2,a,len(self.answers.inverse[a])) for n,a in enumerate(unique_answers)]
        else:
            bet_rows=[(max(len(unique_answers)//2-n,n-len(unique_answers)//2+1)+2,a,len(self.answers.inverse[a])) for n,a in enumerate(unique_answers)]
        bet_rows.insert(0,(6,"smaller",1))
        bet_dict={ans:mult for mult,ans,t in bet_rows}
        await game.send("The Board:\n"+"\n".join("%s to 1: %s x %s" % b for b in bet_rows))
        await dib.gather([self.manage_bets(p,game) for p in self.answers.keys()])
        winning="smaller" if all(u>self.answer for u in unique_answers) else [u for u in unique_answers if u<=self.answer][-1]
        await game.send("The actual answer was %s, so the winning answer was %s!" % (self.answer,winning))
        if winning!="smaller":
            winners=self.answers.inverse[winning]
            await game.send("%s got it right and get %s points!" % (dib.smart_list([p.name for p in winners]),CORRECT))
            for w in winners:
                w.points+=CORRECT
        for p,bets in self.bets.items():
            for b,amount in bets.items():
                if b==winning:
                    await game.send("%s made a correct bet and wins %s!" % (p.name,amount*bet_dict[b]))
                    p.points+=amount+amount*bet_dict[b]
                else:
                    p.points+=min(amount,3-len(bets))
    async def manage_bets(self,player:dib.BasePlayer,game:WitsAndWagers):
        while len(self.bets[player])<2 and player.points:
            msg=await game.wait_for_text(player,"Place a bet (e.g. bet 5 on 3992), or pass. You have %s points left, and can make %s more bets." % (player.points,2-len(self.bets[player])))
            msg=msg.lower()
            if msg=="pass":
                break
            msg=msg.split()
            try:
                bet=int(msg[1])
                answer="smaller" if msg[3]=="smaller" else int(msg[3])
                if answer in self.bets[player]:
                    await player.dm("You've already bet on that! Try thinking harder next time!")
                elif answer!="smaller" and answer not in self.answers.inverse:
                    await player.dm("That's not one of the answers!")
                elif bet>player.points:
                    await player.dm("You don't have enough points left for that bet!")
                elif bet<=0:
                    await player.dm("NO.")
                else:
                    self.bets[player][answer]=bet
                    player.points-=bet
                    await player.dm("Bet successful!")
            except (ValueError,IndexError):
                await player.dm("Incorrect format!")
        await game.send("%s has finished betting!" % player.name)
class WitsAndWagers(dib.BaseGame):
    name="wagers"
    min_players = 4
    max_players = 12
    async def run(self,*modifiers):
        random.shuffle(self.players)
        for p in self.players:
            p.points=2
        for n,p in enumerate(self.players):
            r=Round(p)
            await self.send("ROUND %s/%s\nWaiting for question from %s..." % (n+1,len(self.players),p.name))
            await r.question_phase(self)
            await self.send("The question: %s\nSubmit your guesses!" % r.question)
            await r.answer_phase(self)
            await r.betting_phase(self)
            await self.show_scoreboard(n==len(self.players)-1)
        await self.end_points()

