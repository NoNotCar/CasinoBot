import asyncio
from discord.ext import commands
from economy import get_user
import economy
import random
import itertools
import os
import string
import re
wordlists={}
econv=lambda l:":blue_square:" if l=="*" else ":regional_indicator_%s:" % l.lower()
for file in os.listdir(os.getcwd()+"\\nouns"):
    if file.endswith(".txt"):
        with open(os.getcwd()+"\\nouns\\"+file,"r") as f:
            wordlists[file.split(".")[0]]=[w.replace("\n","") for w in f.readlines()]
class Hangman(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
        self.active=[]
    async def wait_for_input(self,ctx,player,guesses):
        to_delete=[]
        while True:
            m=await ctx.bot.wait_for("message",check=lambda m: m.channel==ctx.channel and m.author==player.user and len(m.content)==1 and m.content in string.ascii_letters)
            letter=m.content.lower()
            to_delete.append(m)
            if letter in guesses:
                to_delete.append(await ctx.send("You've already guessed that!"))
                continue
            return letter,to_delete
    @commands.command(name="hangman",help="Play a game of hangman: costs 1c per incorrect guess, 5c for winning!")
    async def hangman(self,ctx):
        if ctx.channel in self.active:
            await ctx.send("Wait for the current game in this channel to finish!")
            return
        player=get_user(ctx.author)
        if player.credits==0:
            await ctx.send("You're broke and can't play hangman!")
            return
        self.active.append(ctx.channel)
        category=random.choice(list(wordlists.keys()))
        tword=random.choice(wordlists[category])
        cword=["*"]*len(tword)
        guesses=[]
        msg=None
        failed_horribly=False
        while True:
            s="HANGMAN! Category: %s\n" % category+"".join(econv(c) for c in cword)+"\nWrong:"+"".join(econv(c) for c in guesses if c not in cword)
            if msg:
                await msg.edit(content=s)
            else:
                msg=await ctx.send(s)
            if "*" not in cword:
                await ctx.send("Hooray! You got the word! +5c!")
                player.update_balance(5)
                break
            done,not_done=await asyncio.wait([self.wait_for_input(ctx,player,guesses),asyncio.sleep(60)],return_when=asyncio.FIRST_COMPLETED)
            r=next(d for d in done).result()
            if r:
                l,to_delete=r
                for m in to_delete:
                    await asyncio.create_task(m.delete())
                guesses.append(l)
                if l in tword:
                    indices=[m.start() for m in re.finditer(l, tword)]
                    for i in indices:
                        cword[i]=l
                else:
                    player.update_balance(-1)
                    if player.credits==0:
                        await ctx.send("You ran out of money! TOO BAD!")
                        failed_horribly=True
                        break
            else:
                await ctx.send("You spent too long thinking! TOO BAD! NO MONEY!")
                failed_horribly=True
                break
        if failed_horribly:
            await ctx.send("The word was %s" % "".join(econv(l) for l in tword))
        self.active.remove(ctx.channel)

