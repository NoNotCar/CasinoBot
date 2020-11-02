import dib
from discord.ext import commands
from word_list import words
from enum import Enum
import random
from asyncio import create_task,wait_for,exceptions
rtypes=["prefix","suffix","middle"]
fragments={"er","gh","th","sh","de","ed","re","op","py","un","st","ch","po","go","to","so","is","ir","z","v","y","ve","il","oo","ea","ee","in","can","wed","res","x","are","ira","pat","ty","ae","ma","ta","sa"}
def valid(word,rtype,frag):
    l=len(frag)
    if rtype=="any":
        return frag in word
    elif rtype=="prefix":
        return frag==word[:l]
    elif rtype=="suffix":
        return frag==word[-l:]
    return frag in word[1:-1]
class BombPlayer(dib.BasePlayer):
    lives=3
class BombGame(dib.BaseGame):
    current_turn=0
    playerclass = BombPlayer
    done=False
    min_players = 2
    max_players = 20
    name="bomb"
    async def run(self):
        await self.channel.send("PLAYER ORDER: "+" ,".join(p.name for p in self.players))
        p_order=[]
        while len(self.players)>1:
            try:
                await wait_for(self.run_round(),random.uniform(30,60))
            except exceptions.TimeoutError:
                exploded=self.players[self.current_turn]
                await self.channel.send(":boom: BOOM! :boom:")
                exploded.lives-=1
                if exploded.lives:
                    await self.channel.send("%s has %s lives remaining!" % (exploded.name,exploded.lives))
                else:
                    await self.channel.send("%s has sadly died - :exploding_head:" % exploded.name)
                    self.players.remove(exploded)
                    p_order.append([exploded])
        await self.channel.send("THE GAME IS OVER. %s WON AND RECEIVES 10c!" % self.players[0].name)
        self.players[0].user.update_balance(10)
        p_order.append([self.players[0]])
        p_order.reverse()
        await self.end_ranked(p_order)
    async def run_round(self):
        frag=random.choice(list(fragments))
        rt=random.choice(rtypes)
        used=set()
        self.current_turn=random.randint(0,len(self.players)-1)
        await self.channel.send("ROUND START: %s - %s\n%s to play." % (frag.upper(),rt.upper(),self.players[self.current_turn].name))
        while True:
            message = await self.bot.wait_for("message", check=lambda m: m.channel == self.channel and m.content and m.author!=self.bot.user)
            if message.author==self.players[self.current_turn].du:
                word=message.content.lower()
                if word in words:
                    if valid(word,rt,frag):
                        if word in used:
                            create_task(self.channel.send("Already used!"))
                        else:
                            self.current_turn+=1
                            self.current_turn%=len(self.players)
                            used.add(word)
                    else:
                        create_task(self.channel.send("Invalid word!"))
                else:
                    create_task(self.channel.send("Not in the dictionary!"))
            else:
                create_task(self.channel.send("It's %s's turn!" % self.players[self.current_turn].name))