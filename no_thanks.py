import dib
import asyncio
import random

def get_points(cards):
    return sum([c for c in cards if c+1 not in cards])
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
        return self._tokens-get_points(self.cards)
    @property
    def tokens(self):
        return self._tokens
    @tokens.setter
    def tokens(self,new):
        self._tokens=new
        asyncio.create_task(self.update_message())

class NoThanks(dib.BaseGame):
    name="nothanks"
    has_ai = True
    min_players = 2
    max_players = 10
    playerclass = NoThanksPlayer
    def will_take(self,card:int,ctokens:int,player:NoThanksPlayer,remaining_rounds:int):
        if not player.tokens:
            return True
        u = self.get_utility(card,ctokens,player,remaining_rounds)
        mus = max(self.get_utility(card,ctokens,p,remaining_rounds) for p in self.players if p!=player)
        if mus>0:
            return u>0 and random.randint(0,1)
        return u>0
    def get_utility(self,card:int,ctokens:int,player:NoThanksPlayer,remaining_rounds:int):
        token_multiplier = 1+remaining_rounds/random.randint(15,35)+max(0,(11-player.tokens)/random.randint(11,22))
        return ctokens*token_multiplier-(get_points(player.cards+[card])-get_points(player.cards))
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
                if cp.fake:
                    choice = "yes" if self.will_take(current,bounty,cp,len(deck)) else "no"
                    if choice=="no":
                        await self.send(f"{cp.name} refused to take {current}")
                    else:
                        await self.send(f"{cp.name} took {current}!")
                else:
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

