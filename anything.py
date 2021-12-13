import dib
import random
import itertools

class SayAnything(dib.BaseGame):
    min_players = 3
    max_players = 20
    name = "say-anything"
    no_pump = False
    async def run(self,*modifiers):
        rounds = len(self.players)
        random.shuffle(self.players)
        for r in range(rounds):
            qm = self.players[(r+len(self.players)//2+1)%len(self.players)]
            answerer = self.players[r]
            others = [p for p in self.players if p!=answerer]
            await self.send(f"ROUND {r+1}/{rounds}\n {qm.name} is coming up with a question for {answerer.name}.")
            question = await self.wait_for_text(qm,f"Enter a question for {answerer.name}!")
            await self.send(f"{qm.name} has given the question: {question}\nEveryone _but_ {answerer.name}, submit your answers!")
            answers = await dib.smart_gather([self.wait_for_text(o,"Submit your answer!") for o in others],others)
            answers=dib.bidict({p:a.lower() for p,a in answers.items()})
            alist = list(answers.inverse.keys())
            random.shuffle(alist)
            await self.send("Answers:")
            await self.send("\n".join(f"{n+1}:{a}" for n,a in enumerate(alist)))
            if len(alist)==1:
                await self.send(f"{qm.name}, that was a SHITTY QUESTION - everyone submitted the same answer! -1 points!")
                qm.points-=1
            else:
                await self.send(f"Waiting for {answerer.name} to pick their favourite")
                chosen = await self.numbered_options(answerer,alist)
                await self.send("It's BETTING TIME!")
                valid_choices = {str(n+1):(a,) for n,a in enumerate(alist)}
                valid_choices.update({f"{x+1} and {y+1}":(alist[x],alist[y]) for (x,y) in itertools.combinations(range(len(alist)),2)})
                bets = await dib.smart_gather([self.choose_option(o,True,valid_choices.keys(),"What numbers do you want to bet on (max 2)?",True) for o in others],others)
                await self.send(f"The answer {answerer.name} actually picked was {chosen}!")
                writers = answers.inverse[chosen]
                for w in writers:
                    w.points+=1
                await self.send(f"{dib.smart_list([w.name for w in writers])} wrote the correct prompt: +1 points!")
                correct = 0
                for p,bet in bets.items():
                    actual_bet = valid_choices[bet]
                    if chosen in actual_bet:
                        pts = 2 if len(actual_bet)==1 else 1
                        await self.send(f"{p.name} made a correct bet and gets {pts} points!")
                        p.points+=pts
                        correct+=pts
                apts = min(3,correct)
                await self.send(f"{answerer.name} gets {apts} points for correct bets.")
                answerer.points+=apts
            await self.show_scoreboard(r==rounds-1)
        await self.end_points()


