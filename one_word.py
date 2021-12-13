import dib
import random
import asyncio
from word_list import words, common
from similarity.longest_common_subsequence import LongestCommonSubsequence
lcs=LongestCommonSubsequence()
list_words=list(words)
list_common=list(common)
def too_similar(word1,word2):
    if abs(len(word1)-len(word2))>1:
        return False
    longest=max(len(word1),len(word2))
    return lcs.distance(word1,word2)<min(longest-1,2)

class OneWord(dib.BaseGame):
    min_players = 3
    max_players = 20
    name = "oneword"
    CORRECT_BONUS = 50
    async def wait_for_clue(self,player,target):
        clue = await self.choose_option(player, True, words, "Word to guess: %s\nSubmit your clue!" % target, True)
        await self.channel.send("%s has submitted their clue!" % player.name)
        return clue
    async def run(self,*modifiers):
        random.shuffle(self.players)
        rounds=int(modifiers[0]) if modifiers else max(10,len(self.players))
        points=0
        for n in range(rounds):
            guesser=self.players[n%len(self.players)]
            await self.channel.send("ROUND %s/%s: %s to guess." % (n+1,rounds, guesser.name))
            word=random.choice(list_common)
            clues = await asyncio.gather(*[self.wait_for_clue(p,word) for p in self.players if p is not guesser])
            colliding=set()
            for n,c in enumerate(clues):
                for oc in clues[n+1:]:
                    if too_similar(c,oc):
                        colliding.add(c)
                        colliding.add(oc)
            actual_clues=[c for c in clues if c not in colliding and not too_similar(c,word)]
            if actual_clues:
                guess=await self.choose_option(guesser,False,words,"Guessing time! Clues: "+", ".join(actual_clues),True)
                if too_similar(guess,word):
                    await self.channel.send("CORRECT! WELL DONE! You get %sc!" % self.CORRECT_BONUS)
                    guesser.user.update_balance(self.CORRECT_BONUS)
                    points+=1
                else:
                    await self.channel.send("Sorry, the word was actually "+word)
            else:
                await self.channel.send("Sorry, all words collided or were too similar...")
        await self.channel.send("Game over! Your score: %s/%s" % (points,rounds))
        money = 5*(points**2)
        await self.channel.send("All players get %sc!" % money)
        for p in self.players:
            p.user.update_balance(money)
        self.done=True
