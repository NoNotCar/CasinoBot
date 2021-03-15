import dib
from collections import defaultdict,Counter
import asyncio
import random

WHEEL_SIZE = 36
class Roulette(dib.BaseGame):
    bets_closed = False
    all_play = True
    valid_bets = {str(n):({n},WHEEL_SIZE) for n in range(0,WHEEL_SIZE+1)}
    valid_bets.update({eo:({n for n in range(1,WHEEL_SIZE+1) if n%2==parity},2) for eo,parity in (("odd",1),("even",0))})
    valid_bets.update({"low":(set(range(1,19)),2),"high":(set(range(19,37)),2)})
    valid_bets.update({"1st dozen": (set(range(1, 13)), 3), "2nd dozen": (set(range(13,25)), 3),"3rd dozen": (set(range(25, 37)), 3)})
    no_pump = False
    MIN_TIME = 30
    MAX_TIME = 60
    name = "roulette"
    unstoppable = True
    def __init__(self,ctx):
        super().__init__(ctx)
        self.bets=defaultdict(Counter)
    async def bet(self,player:dib.BasePlayer,amount:int,on:str,thing:str):
        if self.bets_closed:
            await self.send("BETS ARE CLOSED! TOO BAD! also this is a bug and shouldn't appear.")
        if on!="on":
            return
        if amount<1:
            await self.send("Can't bet less than 1c!")
            return
        if thing in self.valid_bets:
            if player.user.update_balance(-amount):
                self.bets[player][thing]+=amount
                await self.send("Bet successful!")
            else:
                await self.send("You're TOO POOR to bet that much!")
        else:
            await self.send("Not a valid bet...")
    async def run(self,*modifiers):
        await self.send("The ball is rolling! PLACE YOUR BETS!")
        bet_manager = asyncio.create_task(self.run_pseudocommands(self.bet))
        await asyncio.sleep(random.randint(self.MIN_TIME,self.MAX_TIME))
        bet_manager.cancel()
        self.bets_closed=True
        landed=random.randint(0,WHEEL_SIZE)
        await self.send(f"The ball landed on {landed}!")
        winnings = Counter()
        for p,bets in self.bets.items():
            for bet,amount in bets.items():
                if landed in self.valid_bets[bet][0]:
                    winnings[p]+=self.valid_bets[bet][1]*(amount-1)
                    p.user.update_balance(self.valid_bets[bet][1]*amount)
                else:
                    winnings[p]-=amount
        await self.send("WINNINGS THIS GAME:")
        await self.send("\n".join(f"{p.name}:{w}" for p,w in winnings.items()))
        await self.pump()
        self.done=True

