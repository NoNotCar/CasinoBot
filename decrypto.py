import dib
import discord
from itertools import permutations
import random
from word_list import common
import asyncio

possible_codes = [list(p) for p in permutations([1, 2, 3, 4], 3)]
LEEWAY = 60
def stripsplit(string:str,sep:str):
    return [s.strip() for s in string.split(sep)]
def get_valid_clue(clue:str):
    split=stripsplit(clue,",")
    if len(split)==3 and all(split):
        return split
def get_guess(guess:str):
    split = stripsplit(guess,",")
    try:
        if len(set(split)) == 3 and all(0<int(s)<5 for s in split):
            return [int(s) for s in split]
    except ValueError:
        return False
def random_guess():
    return ",".join(str(i) for i in random.choice(possible_codes))
class GameState(object):
    def __init__(self,left_emoji,right_emoji):
        self.emojis=[left_emoji,right_emoji]
        self.past_words=[{},{}]
    def get_embeds(self):
        for n in range(2):
            embed=discord.Embed(title="%s: Past Clues" % self.emojis[n])
            for w in range(1,5):
                if w in self.past_words[n]:
                    embed.add_field(name="Word %s" % w,value="\n".join(self.past_words[n][w]))
            yield embed
    def add_clue(self,team:int,word:int,clue:str):
        if word not in self.past_words[team]:
            self.past_words[team][word]=[clue]
        else:
            self.past_words[team][word].append(clue)
class Decrypto(dib.BaseGame):
    name = "decrypto"
    min_players = 4
    async def run(self,*modifiers):
        agnijo = "agnijo" in modifiers
        if agnijo:
            await self.send(":warning::sleeping::warning: TIMER DISABLED :warning::sleeping::warning:")
        gs=GameState(":red_circle:",":blue_circle:")
        random.shuffle(self.players)
        left_team = self.players[::2]
        right_team=self.players[1::2]
        codewords=random.sample(common,8)
        teams=left_team,right_team
        codemaster=[0,0]
        intercepts=[0,0]
        miscoms=[0,0]
        await self.send("Team %s: %s\nTeam %s: %s" % (gs.emojis[0],dib.smart_list([p.name for p in left_team]),gs.emojis[1],dib.smart_list([p.name for p in right_team])))
        for n in range(2):
            for p in teams[n]:
                await p.dm("Your codewords:\n"+"\n".join(dib.to_emoji(i+1)+": "+codewords[i*2+n].upper() for i in range(4)))
        for r in range(8):
            codemasters=[left_team[codemaster[0]],right_team[codemaster[1]]]
            await self.send("ROUND %s/8: Codemasters: %s and %s" % (r+1,codemasters[0].name,codemasters[1].name))
            codes = [random.choice(possible_codes) for _ in range(2)]
            clues = [None, None]
            tasks=[self.wait_for_text(p,"Sequence to send: "+"".join(dib.to_emoji(c) for c in codes[n])+"\nSubmit your clue, comma separated.",
                                      validation=get_valid_clue,
                                      confirmation="%s has submitted their clues!",
                                      faked="dog,cat,horse") for n,p in enumerate(codemasters)]
            tasks=[asyncio.create_task(t) for t in tasks]
            await asyncio.wait(tasks,return_when=(asyncio.ALL_COMPLETED if agnijo else asyncio.FIRST_COMPLETED))
            try:
                not_done = next(t for t in tasks if not t.done())
                nidx = tasks.index(not_done)
                await self.send("%s, you have %s seconds to submit your clue!" % (codemasters[nidx].tag,LEEWAY))
                await asyncio.wait_for(not_done,LEEWAY)
            except StopIteration:
                pass
            except asyncio.TimeoutError:
                await self.send("Oh no! %s did not submit clues in time..." % codemasters[nidx].name)
            for n,t in enumerate(tasks):
                if not t.cancelled():
                    clues[n]=t.result()
            for e in gs.get_embeds():
                await self.send(embed=e)
            guesses=None
            if r:
                await self.send("Interception time!\n%s's clues: %s.\n%s's clues: %s" % (gs.emojis[0],clues[0] or "Not submitted",gs.emojis[1],clues[1] or "Not submitted"))
                guesses=await dib.gather([self.wait_for_text(teams[n],"",False,get_guess,"%s's team submitted their guess!",random_guess()) for n in range(2)])
                guesses=[get_guess(g) for g in guesses]
            await self.send("Guessing time!\n%s's clues: %s.\n%s's clues: %s" % (gs.emojis[0], clues[0] or "Not submitted", gs.emojis[1], clues[1] or "Not submitted"))
            results = await dib.gather([self.wait_for_text([p for p in teams[n] if p != codemasters[n]], "", False,get_guess, "%s's team submitted their guess!",random_guess()) for n in range(2)])
            results=[get_guess(r) for r in results]
            failure=False
            for n in range(2):
                codemaster[n]+=1
                codemaster[n]%=len(teams[n])
                for idx,w in enumerate(codes[n]):
                    if clues[n]:
                        gs.add_clue(n,w,get_valid_clue(clues[n])[idx])
            for n,e in enumerate(gs.emojis):
                if guesses and guesses[n]==codes[1-n]:
                    intercepts[n]+=1
                    await self.send("%s intercepted!" % e)
                    failure=True
                if results[n]!=codes[n]:
                    miscoms[n]+=1
                    await self.send("%s miscommunicated! The clue was actually %s" % (e,"".join(dib.to_emoji(c) for c in codes[n])))
                    failure=True
            if not failure:
                await self.send("Both teams were successful!")
            if any(t==2 for t in intercepts+miscoms):
                break
            await self.send("The game continues...\nCurrent miscommunications: %s\nCurrent interceptions: %s" % ("-".join(str(m) for m in miscoms),"-".join(str(i) for i in intercepts)))
            for e in gs.get_embeds():
                await self.send(embed=e)
        totals = [intercepts[n] ** 2 - miscoms[n] ** 2 for n in range(2)]
        for e in gs.get_embeds():
            await self.send(embed=e)
        if totals[0] > totals[1]:
            await self.send("%s wins!" % gs.emojis[0])
            await self.end_game(left_team)
        elif totals[1] > totals[0]:
            await self.send("%s wins!" % gs.emojis[1])
            await self.end_game(right_team)
        else:
            await self.send("It's a draw!")
            await self.end_game(right_team, draw=True)


