import dib
import random
import word_list
import asyncio
import typing
from collections import Counter

LIVES = 3
class Insider(dib.BaseGame):
    name = "insider"
    max_players = 20
    min_players = 4
    async def accuse_phase(self,guessers:typing.List[dib.BasePlayer],voters:typing.List[dib.BasePlayer],trole:str):
        await dib.gather([p.dm(f"Who's the {trole}?") for p in voters])
        votes = await dib.gather([self.dm_tag(p,[op for op in guessers if op!=p]) for p in voters])
        vfor = Counter(votes)
        mx = max(vfor.values())
        maxed = [p for p,v in vfor.items() if v==mx]
        if len(maxed)==1:
            return maxed[0]
        return None
    async def run(self,*modifiers):
        rounds = 3
        for n in range(rounds):
            normies = self.players.copy()
            random.shuffle(normies)
            master = normies.pop()
            insider = normies.pop()
            impostor = normies.pop()
            guessers = normies+[insider,impostor]
            await self.send(f"Round {n+1}/{rounds}. The Master is {master.name}.")
            word_choice = random.sample(word_list.common,5)
            word = await self.choose_option(master,True,word_choice,"Choose a word for the other players to guess: ")
            await insider.dm(f"You are the Insider. The word is {word}. Help the other players guess it, but don't reveal yourself!")
            await impostor.dm(f"You are the Impostor. The word is {word}. Lead the players down the wrong track, or use up all their lives!")
            timer = dib.TextTimer(300,self.channel,"Question Time! Time remaining: %s")
            success = False
            for life in range(LIVES):
                await self.send("Lives remaining: "+":heart:"*(LIVES-life))
                guess = asyncio.create_task(self.wait_for_text(guessers,"",False))
                done,pending = await asyncio.wait((guess,timer.run()),return_when=asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()
                if timer.done:
                    await self.send("TIME'S UP!")
                    break
                else:
                    g = guess.result()
                    if g.lower()==word.lower():
                        await self.send("CORRECT!")
                        success=True
                        break
                    else:
                        await self.send("WRONG! You lose a life!")
            else:
                await self.send("Oh no, you're out of lives...")
            if success:
                await self.send("You may have gotten the word, but who's the Insider? Discuss and guess when ready!")
                await self.send(f"({impostor.name} failed in their mission and so can't vote or be voted for)")
                accused = await self.accuse_phase(normies+[insider],normies+[master,insider],"Insider")
                if accused==insider:
                    await self.send(f"Correct! {insider.name} was the Insider!")
                    for n in normies+[master]:
                        n.points+=1
                elif accused:
                    await self.send(f"Incorrect! You voted for {accused.name}, but {insider.name} was the Insider!")
                    insider.points+=1
                else:
                    await self.send(f"Oh no! The vote was a tie, so the Insider wins! ({insider.name} was the Insider)")
                    insider.points+=1
            else:
                await self.send("You didn't get the word, but can you stop the Impostor getting away with it? Discuss and guess when ready!")
                accused=await self.accuse_phase(guessers,self.players,"Impostor")
                if accused==impostor:
                    await self.send(f"Correct! {insider.name} was the Insider and {impostor.name} was the Impostor!")
                elif accused:
                    await self.send(f"Incorrect! You voted for {accused.name}, but {insider.name} was the Insider and {impostor.name} was the Impostor!")
                    impostor.points+=1
                else:
                    await self.send(f"Oh no! The vote was a tie, so the Impostor wins! ({insider.name} was the Insider and {impostor.name} was the Impostor)")
                    impostor.points+=1
            await self.show_scoreboard(n==rounds-1)
        await self.end_points()