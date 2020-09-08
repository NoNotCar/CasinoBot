import asyncio
from discord.ext import commands
from economy import get_user
import economy
import random
import itertools
from collections import Counter
import math
import re
import word_list
words=set(w for w in word_list.words if len(w)<10)
econv=lambda l:":asterisk:" if l=="*" else ":regional_indicator_%s:" % l.lower() if isinstance(l,str) else str(l)
searchlist=list(words)
random.shuffle(searchlist)
searchlist=sorted(searchlist,key=len,reverse=True)
task=asyncio.create_task
operators=["+","-","*","/","(",")"]
numerals=[str(n) for n in range(10)]
regexPattern = '|'.join(map(re.escape, operators))
def spellable(w1,w2):
    if "*" in w2:
        w2=w2[:]
        w2.remove("*")
        return any(spellable([w for n,w in enumerate(w1) if n!=m],w2) for m,_ in enumerate(w1))
    c1,c2=Counter(w1),Counter(w2)
    return set(w1)<=set(w2) and all(c1[k]<=c2[k] for k in c1.keys())
def recursive_maths(numbers):
    if len(numbers)==2:
        a,b=numbers
        try:
            return Counter(int(n) for n in [a+b,abs(a-b),a*b,a/b,b/a] if round(n)==n)
        except ZeroDivisionError:
            return Counter(int(n) for n in [a+b,abs(a-b),a*b,0])
    else:
        result=Counter()
        combs=list(itertools.combinations(numbers,2))
        random.shuffle(combs)
        combs=combs[:len(combs)//2]
        for c in combs:
            others=[]
            for n in numbers:
                if numbers.count(n)-others.count(n)-c.count(n)>0:
                    others.append(n)
            for n in recursive_maths(c):
                result.update(recursive_maths([n]+others))
        return result
class Countdown(commands.Cog):
    winnings={"easy":2,"medium":5,"hard":10,"extreme":20,"mathmo":50}
    time={"easy":30,"medium":45,"hard":60,"extreme":90,"mathmo":120}
    def __init__(self,bot):
        self.games=[]
        self.bot=bot
    async def manage_countdown(self,ctx,letters,time,t_int=5,target=None):
        joiner="" if isinstance(letters[0],str) else ","
        second_line=joiner.join(econv(l) for l in letters)
        if target:
            second_line+="   TARGET: %s" % target
        msg=await ctx.send("COUNTDOWN HAS STARTED. TIME LEFT: %s\n" % time+second_line)
        while True:
            await asyncio.sleep(t_int)
            time-=t_int
            if time<=0:
                break
            await msg.edit(content="COUNTDOWN HAS STARTED. TIME LEFT: %s:\n" % time+second_line)
        await msg.edit(content="TIME'S UP FOLKS!\n"+second_line)
    async def maths_input(self,ctx,numbers,target):
        while True:
            m= await ctx.bot.wait_for("message",check=lambda m: m.channel==ctx.channel and m.author!=ctx.bot.user and m.content and all(s in operators+numerals+["x"] for s in m.content))
            player=get_user(m.author)
            content=m.content.replace("x","*")
            if "//" in content:
                task(ctx.send("Floor division is not allowed!"))
                continue
            if "**" in content:
                task(ctx.send("Powers are not allowed!"))
                continue
            numbers_used=[int(n) for n in re.split(regexPattern,content) if n]
            if not spellable(numbers_used,numbers):
                task(ctx.send("Incorrect numbers!"))
                continue
            try:
                result=eval(content)
                if result==target:
                    return player
                else:
                    task(ctx.send("Incorrect result: %s!" % result))
                    continue
            except Exception:
                task(ctx.send("Something went wrong while executing your answer..."))
                continue
    async def user_input(self,ctx,letters,udict):
        done=set()
        while True:
            m= await ctx.bot.wait_for("message",check=lambda m: m.channel==ctx.channel and m.author!=ctx.bot.user and m.content and " " not in m.content and "?" not in m.content)
            player=get_user(m.author)
            content=m.content.lower()
            if content in done:
                task(ctx.send("Someone's already got that word!"))
                continue
            if player in udict and len(udict[player])>=len(content):
                task(ctx.send("You've got a word of equal or greater length already!"))
                continue
            if spellable(content,letters):
                if content in words:
                    mx=(max(len(w) for w in udict.values()) if udict else 0)
                    if len(content)>mx:
                        task(ctx.send("%s has the new longest word!" % player.nick))
                    elif len(content)==mx:
                        task(ctx.send("%s has equalled the longest word!" % player.nick))
                    else:
                        task(ctx.send("%s has got a word of length %s" % (player.nick,len(content))))
                    udict[player]=content
                    done.add(content)
                else:
                    task(ctx.send("That word is not in the dictionary!"))
            else:
                task(ctx.send("not spellable using these letters..."))
    @commands.command(name="countdown",help="Play countdown, costs 1 credit. You can also do ?countdown wild for 2 credits")
    async def countdown(self,ctx,wild="normal"):
        await self.play(ctx,None,wild=="wild")
    async def play(self,ctx,conundrum=None,wild=False):
        cost=5 if conundrum else 2 if wild else 1
        if ctx.channel in self.games:
            await ctx.send("Game already running in this channel!")
            return
        if not get_user(ctx.author).update_balance(-cost):
            await ctx.send("You're _too poor_ for countdown!")
            return
        self.games.append(ctx.channel)
        letters=list(conundrum if conundrum else random.sample(word_list.ldist,9))
        random.shuffle(letters)
        if wild:
            letters[8]="*"
        udict={}
        longest_word=conundrum if conundrum else next(w for w in searchlist if spellable(w,letters))
        t1,ui=await asyncio.wait([self.manage_countdown(ctx,letters,30),self.user_input(ctx,letters,udict)],return_when=asyncio.FIRST_COMPLETED)
        for u in ui:
            u.cancel()
        s="Game finished! Longest word possible: %s" % longest_word
        win_word=max(len(w) for w in udict.values()) if udict else None
        winners=[u for u,w in udict.items() if len(w)==win_word]
        for u,w in udict.items():
            winnings=20 if len(w)==9 else 8 if len(w)==8 else 5 if len(w)==len(longest_word) else 2 if len(w)==len(longest_word)-1 else 0
            if u in winners and len(udict)>1:
                winnings+=2
            s+="\n%s %s a word of length %s. They get %sc" % (u.nick,"won with" if u in winners else "got",len(w),winnings)
            u.update_balance(winnings)
        await ctx.send(s)
        self.games.remove(ctx.channel)
    @commands.command(name="conundrum",help="Play a countdown where a 9 letter word is guaranteed possible, costs 5 credits")
    async def conundrum(self,ctx):
        word=random.choice([w for w in words if len(w)==9])
        await self.play(ctx,word)
    @commands.command(name="maths",help="Play a maths round! Also costs 1c.")
    async def maths(self,ctx,difficulty="medium"):
        try:
            target={"easy":0.1,"medium":0.5,"hard":0.9,"extreme":1.0,"mathmo":1.0}[difficulty]
        except KeyError:
            await ctx.send("not a valid difficulty!")
            return
        if not get_user(ctx.author).update_balance(-1):
            await ctx.send("You're _too poor_ for countdown!")
            return
        numbers=random.choices(list(range(1,10)),k=4)+random.choices([10,25,50,75,100],k=2)
        results={k:v for k,v in recursive_maths(numbers).items() if (1000<=k<9999 if difficulty=="mathmo" else 100<=k<999)}
        results=sorted(((k,v) for k,v in results.items()), key=lambda p:p[1],reverse=True)
        results=[r[0] for r in results]
        target=results[int(min(len(results)*target,len(results)-1))]
        done, not_done = await asyncio.wait([self.manage_countdown(ctx, numbers, self.time[difficulty],target=target), self.maths_input(ctx,numbers,target)],return_when=asyncio.FIRST_COMPLETED)
        winner=next(d for d in done).result()
        next(d for d in not_done).cancel()
        if winner:
            winnings=self.winnings[difficulty]
            await ctx.send("Well done %s! You won %sc!" % (winner.nick,winnings))
            winner.update_balance(winnings)
        else:
            await ctx.send("Nobody won...")

