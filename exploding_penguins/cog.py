import asyncio
import discord
from discord.ext import commands
from . import mechanics,cards
class Penguins(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
        self.games={}
    @commands.command("penguins",help="join a game in this channel")
    async def start(self,ctx):
        if ctx.channel in self.games:
            if isinstance(self.games[ctx.channel],list) and ctx.author not in self.games[ctx.channel]:
                self.games[ctx.channel].append(ctx.author)
                await ctx.send("Join successful. Total players: %s" % len(self.games[ctx.channel]))
            else:
                await ctx.send("no")
        else:
            self.games[ctx.channel]=[]
            await self.start(ctx)
    @commands.command("waddle",help="start the game")
    async def start_game(self,ctx):
        if ctx.channel in self.games:
            g=self.games[ctx.channel]
            if isinstance(g,list):
                await self.games[ctx.channel].run(ctx.channel,self.bot)
                del self.games[ctx.channel]
            else:
                await ctx.send("Game already started!")
        else:
            await ctx.send("No game in this channel...")
