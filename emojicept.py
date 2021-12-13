import dib
import word_list
import random
from one_word import too_similar

class Emojicept(dib.BaseGame):
    min_players = 3
    max_players = 20
    name = "emojicept"
    no_pump = False
    async def run(self,*modifiers):
        qm="qm" in modifiers
        if qm:
            await self.send("QM mode activated!")
        random.shuffle(self.players)
        for n,describer in enumerate(self.players):
            qm = self.players[(n+len(self.players)//2+1)%len(self.players)] if qm else None
            if qm:
                await self.send(f"Round {n+1}/{len(self.players)}. Question Master: {qm.name}, Describer: {describer.name}")
                concept = await self.wait_for_text(qm,f"Give a concept for {describer.name} to emojify!")
            else:
                await self.send(f"Round {n+1}/{len(self.players)}. Describer: {describer.name}")
                choices = random.sample(word_list.common,3)
                concept=await self.choose_option(describer,True,choices,"Choose a word to emojify: ")
            emoji = await self.wait_for_text(describer,f"Describe {concept} using only emoji! Don't {''.join(dib.to_emoji(c) for c in 'cheat')}!")
            guessers = [p for p in self.players if p not in [qm,describer]]
            await self.send(f"{describer.name}'s clue: {emoji}. Guessing time!")
            guesses = await dib.smart_gather([self.wait_for_text(g,"Submit your guess!") for g in guessers],guessers)
            winners = [p for p,g in guesses.items() if too_similar(g.lower(),concept.lower())]
            await self.send(f"The concept was: \"{concept}\"!")
            if winners:
                await self.send(f"{dib.smart_list(w.name for w in winners)} got it right, and get 1 point! {describer.name} gets 2 points!")
                for w in winners:
                    w.points+=1
                describer.points+=2
            else:
                if qm:
                    await self.send(f"Nobody got it right! {qm.name} loses a point for his shitty concept!")
                    qm.points-=1
                else:
                    await self.send("Nobody got it right! No points!")
            await self.show_scoreboard(n==len(self.players)-1)
        await self.end_points()