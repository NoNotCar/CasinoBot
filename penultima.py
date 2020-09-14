import asyncio
import discord
import random
import itertools
import pickle
import trueskill
from collections import defaultdict
from backend.Vector import Vector2 as V
from discord.ext import commands
from backend import Chess, Pieces
import dib
validcols=[(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255),(255,128,0),
           (255,255,128),(128,255,0),(128,255,255),(128,0,255),(255,128,255),
           (255,0,128),(0,255,128),(0,128,255)]
class Competitor(dib.BasePlayer):
    def __init__(self,user,fake=False):
        super().__init__(user,fake)
        self.col=random.choice(validcols)
        validcols.remove(self.col)
validcolumns="abcdefgh"
validrows="12345678"
def pos_to_v(pos):
    if pos[0] in validcolumns and pos[1] in validrows:
        return V(validcolumns.index(pos[0]),validrows.index(pos[1]))
    raise ValueError("not a valid pos")

class Penultima(dib.BaseGame):
    name="chessx"
    max_players = 2
    min_players = 2
    playerclass = Competitor
    async def run(self,*modifiers):
        random.shuffle(self.players)
        match=Chess.Match(self.players,V(8,8))
        while not match.done:
            img=match.render(3)
            img.save("temp.png")
            turn,other =self.players[match.turn],self.players[not match.turn]
            await self.channel.send("It's %s's turn!" % turn.name,file=discord.File("temp.png"))
            while True:
                message=await self.wait_for_text(turn,"Make a move, ask for info or offer a draw.",False)
                if message[0]=="$":
                    continue
                split = message.split(" ")
                if split[0]=="info":
                    try:
                        pos=pos_to_v(split[1])
                        if match.b[pos]:
                            pname = match.b[pos].name
                            await self.channel.send("%s: %s" % (pname, Pieces.pexp[pname]))
                        else:
                            await self.channel.send("There's no piece there!")
                    except IndexError:
                        await self.channel.send("You have to specify a square!")
                    except ValueError:
                        await self.channel.send("Invalid square!")
                elif split[0]=="draw":
                    result=await self.choose_option(other,False,["yes","no"],"%s, %s has offered a draw. Do you accept?" % (other.name,turn.name))
                    if result=="yes":
                        await self.channel.send("Draw accepted! No prize for draws!")
                        await self.end_game([turn],[other],True)
                        return
                    else:
                        await self.channel.send("Sorry, guess you'll have to resign or something :P")
                elif split[0]=="resign":
                    await self.channel.send("Oh no! You resigned! %s gets 10c!" % other.name)
                    other.user.update_balance(10)
                    await self.end_game([other],[turn])
                    return
                elif len(split)==2:
                    try:
                        poss=[pos_to_v(p.lower()) for p in split]
                        if match.on_move(*poss):
                            if match.done:
                                await self.channel.send("You won! Well done! You win 10c!")
                                turn.user.update_balance(10)
                                await self.end_game([turn],[other])
                                return
                            break
                        else:
                            await self.channel.send("Not a valid move, try info [pos] for help!")
                    except ValueError:
                        await self.channel.send("Those aren't valid board positions...")
