import dib
import random
from asyncio import sleep

class TurboPlayer(dib.BasePlayer):
    drawing=False
class Prompt(object):
    locked=False
    def __init__(self):
        self.chain=[]
    def valid(self,player:TurboPlayer,turbo=False):
        return not self.locked and not any(p==player for p,_ in self.chain) and (turbo or player.drawing==self.drawing)
    async def show(self, tchannel):
        for n, (p,t) in enumerate(self.chain):
            if not n:
                await tchannel.send('ORIGINAL PROMPT: "%s", Submitted by %s' % (t, p.name))
            elif n % 2:
                await tchannel.send("%s then drew it:\n%s" % (p.name, t))
            else:
                await tchannel.send("%s described it as %s" % (p.name, t))
            if not p.fake:
                await sleep(8)
    @property
    def drawing(self):
        return len(self.chain)%2
class Turbostrations(dib.BaseGame):
    name="turbostrations"
    prompts=None
    target=0
    async def run(self,*modifiers):
        self.target = int(modifiers[0]) if modifiers else len(self.players)
        self.prompts=[]
        random.shuffle(self.players)
        await dib.gather([self.manage_player(p) for p in self.players])
        for p in self.prompts:
            await p.show(self.channel)
        for p in self.players:
            p.user.update_balance(10)
        await self.channel.send("Well done everyone! You all get 10c for participating!")
        self.done=True
    async def manage_player(self,player:TurboPlayer):
        prompt=Prompt()
        prompt.chain.append((player,await self.wait_for_text(player,"Submit your prompt!")))
        await player.dm("Thanks!")
        self.prompts.append(prompt)
        while not all(len(p.chain)==self.target for p in self.prompts):
            for p in self.prompts:
                if p.valid(player,True):
                    p.locked=True
                    if p.drawing:
                        p.chain.append((player,await self.wait_for_picture(player,"Draw this: %s" % p.chain[-1][1])))
                    else:
                        p.chain.append((player,await self.wait_for_text(player,"Describe this:\n%s" % p.chain[-1][1])))
                    await player.dm("Thanks!")
                    p.locked=len(p.chain)>=self.target
            await sleep(1)
