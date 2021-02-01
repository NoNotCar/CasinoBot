import dib
import asyncio
import random

class NoThanksPlayer(dib.BasePlayer):
    _tokens = 11
    tmsg = None
    def __init__(self,user,fake=False):
        super().__init__(user,fake)
        self.cards = []
    async def update_message(self):
        if self.tmsg:
            await self.tmsg.edit(content="Current tokens: %s" % self._tokens)
        else:
            self.tmsg=await self.dm("Current tokens: %s" % self._tokens)
    @property
    def points(self):
        return self._tokens-sum([c for c in self.cards if c+1 not in self.cards])
    @property
    def tokens(self):
        return self._tokens
    @tokens.setter
    def tokens(self,new):
        self._tokens=new
        asyncio.create_task(self.update_message())

class NoThanks(dib.BaseGame):
    name="nothanks"
    min_players = 2
    max_players = 10
    playerclass = NoThanksPlayer
    async def run(self,*modifiers):
        random.shuffle(self.players)
        for p in self.players:
            await p.update_message()
        deck = random.sample(range(3,36),24)
        turn = 0
        while deck:
            current = deck.pop()
            info = "\n".join("%s: %s" % (p.name, ", ".join(str(c) for c in p.cards)) for p in self.players if p.cards)
            await self.send(info+"\nThe next card is: %s" % current)
            bounty = 0
            while True:
                cp = self.players[turn]
                choice = await self.choose_option(cp,False,["yes","no"] if cp.tokens else ["yes"],"%s, do you wish to take it? (Current tokens: %s)" % (cp.tag,bounty),True)
                if choice=="no":
                    bounty+=1
                    cp.tokens-=1
                    turn+=1
                    turn%=len(self.players)
                else:
                    cp.cards.append(current)
                    cp.cards.sort()
                    cp.tokens+=bounty
                    break
        await self.show_scoreboard(True)
        await self.end_points()

