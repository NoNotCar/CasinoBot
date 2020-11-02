from dib import BaseGame, BasePlayer, smart_number
import asyncio
import random

class Prompt(object):
    def __init__(self,text):
        self.pages=[text]
    async def show(self,tchannel,players,idx):
        for n, t in enumerate(self.pages):
            p=players[(idx+n)%len(players)]
            if not n:
                await tchannel.send('ORIGINAL PROMPT: "%s", Submitted by %s' % (t, p.name))
            elif n%2:
                await tchannel.send("%s then drew it:\n%s" % (p.name,t))
            else:
                await tchannel.send("%s described it as %s" % (p.name, t))
            if not p.fake:
                await asyncio.sleep(8)
    @property
    def current(self):
        return self.pages[-1]
    @property
    def writing(self):
        return not len(self.pages)%2
    @property
    def age(self):
        return len(self.pages)
class Telestrator(BasePlayer):
    def __init__(self,user,fake=False):
        super().__init__(user,fake)
        self.queue=[]

class Telestrations(BaseGame):
    playerclass = Telestrator
    name="telestrations"
    target_length=7
    async def run(self,*modifiers):
        random.shuffle(self.players)
        try:
            self.target_length=int(modifiers[0]) if modifiers else (len(self.players)+1)//2*2-1
        except ValueError:
            self.target_length=(len(self.players)+1)//2*2-1
        await self.channel.send("Game length set to %s!" % self.target_length)
        prompts=await asyncio.gather(*[self.manage_player(n) for n,p in enumerate(self.players)])
        for n,p in enumerate(prompts):
            await p.show(self.channel,self.players,n)
        self.done=True
        await self.channel.send("Well done everyone! You all get 10c for participating!")
        for p in self.players:
            p.user.update_balance(10)
    async def manage_player(self,idx):
        p=self.players[idx]
        next_p=self.players[(idx+1)%len(self.players)]
        prompt=Prompt(await self.wait_for_text(p,"Submit your prompt: "))
        await p.dm("Thanks!")
        next_p.queue.append(prompt)
        while True:
            if p.queue:
                next_prompt=p.queue.pop(0)
                if p.queue:
                    await p.dm("Hurry up! There are currently %s in your queue..." % smart_number(p.queue,"prompt"))
                if next_prompt.age==self.target_length:
                    return prompt
                if next_prompt.writing:
                    next_prompt.pages.append(await self.wait_for_text(p,"Describe this:\n"+next_prompt.current))
                else:
                    next_prompt.pages.append(await self.wait_for_picture(p, "Draw this: " + next_prompt.current))
                await p.dm("Thanks!")
                next_p.queue.append(next_prompt)
            else:
                await asyncio.sleep(1)





