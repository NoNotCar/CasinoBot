import discord
from discord.ext import commands
import slots
import economy
import countdown
import hangman
import jukebox
import os
import cards
import pass_the_bomb
from exploding_penguins import game as penguins
import telestrations
import turbostrations
import one_word
from secret_hitler import game as shitler
import penultima
from among_us import game
import drawful
from codenames import codenames
from scrabble import scrabble
import witswagers
import decrypto
import quiplash
from avalon import avalon
from mafia import mafia
from dixit import dixit
import haiclue
import no_thanks
import boggle
import forsale
import spyfall
import red7
from onenight import game
from dominion import base
from snakeoil import snakeoil
import cockroach
from wavelength import wavelength
import insider
import dib
from bottoken import token
import traceback
import casino
import shop
bot=economy.bot
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="the economy like a fiddle"))
@bot.event
async def on_message(message):
    ctx = await bot.get_context(message)
    await bot.invoke(ctx)
@bot.event
async def on_command_error(ctx:commands.Context,error:commands.CommandError):
    if isinstance(error,commands.BadArgument):
        await ctx.send("BAD ARGUMENT: Use $help [command] for help!")
    elif isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("MISSING ARGUMENT: Use $help [command] for help!")
    elif isinstance(error,commands.CommandNotFound):
        await ctx.send("Command not found...")
    elif isinstance(error,commands.NotOwner):
        await ctx.send("You need your name to be yellow to use that! :P")
    elif isinstance(error,commands.CheckFailure):
        await ctx.send("You're probably not an admin or something")
    else:
        raise error
        #await ctx.send("an error occurred...\n"+repr(error))

@bot.command(name="roll",help="roll a dice")
async def roll(ctx,sides:int):
    await ctx.send("You rolled a %s!" % (sides+1))
# @bot.command(name="jenn",help="idk")
# async def jenn(ctx):
#     name = ctx.author.nick
#     await ctx.send(f"""Shall {name} compare jenn to a summer’s day?
# Jenn art more lovely and more temperate:
# Rough winds do shake the darling buds of May,
# And summer’s lease hath all too short a date;
# Sometime too hot the eye of heaven shines,
# And often is his gold complexion dimm'd;
# And every fair from fair sometime declines,
# By chance or nature’s changing course untrimm'd;
# But jenn's eternal summer shall not fade,
# Nor lose possession of that fair jenn ow’st;
# Nor shall death brag jenn wander’st in his shade,
# When in eternal lines to time jenn grow’st:
#    So long as men can breathe or eyes can see,
#    So long lives this, and this gives life to jenn.""")
@bot.command(name="daniel",help="gently persuade Daniel to return to us")
async def daniel(ctx):
    await ctx.send("""@panDANIELlo:rainbow: whence shall we hear your joyful voice again
as the flowers sweetly bloom in the meadow
and children frolic to and fro
lest we forget that gay summer's day
perched on a porcelain throne""")
@bot.command(name="mute",help="server mute yourself")
@commands.has_permissions(administrator=True)
async def mute(ctx):
    await ctx.author.edit(mute=True)
@bot.command(name="begone",help="Stop the bot")
@commands.has_permissions(administrator=True)
async def begone(ctx):
    for c in bot.cogs:
        cog=bot.get_cog(c)
        if isinstance(cog,jukebox.Jukebox):
            await cog.graceful_stop()
    await ctx.send("bye!")
    await bot.logout()
bot.add_cog(slots.Slots(bot))
bot.add_cog(economy.Economy(bot))
bot.add_cog(countdown.Countdown(bot))
bot.add_cog(hangman.Hangman(bot))
bot.add_cog(dib.Games(bot))
bot.add_cog(jukebox.Jukebox(bot))
bot.add_cog(shop.Shop(bot))
bot.run(token)