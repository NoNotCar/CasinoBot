from __future__ import annotations
import typing
import dib
import importlib
import random
import asyncio
from collections import defaultdict

class Role(object):
    phase = None
    singleton = False
    team = "none"
    evil=False
    desc = "_Someone_ didn't bother writing in your rules, figure it out yourself!"
    def __init__(self,user:typing.Optional[ONP]):
        self.user=user
    async def setup(self,game:OneNight):
        pass
    async def preload(self,game:OneNight):
        pass
    async def execute(self, game: OneNight, phase:float):
        pass
    async def on_death(self,game:OneNight,player:ONP):
        pass
    def did_win(self,game:OneNight,player:ONP):
        return True
    @classmethod
    def set_valid(cls, rset: typing.List[typing.Type[Role]], final:bool):
        if cls.singleton:
            return rset.count(cls)<=1
        return True
    @property
    def phases(self)->typing.List[int]:
        return [self.phase] if self.phase else []
    @property
    def name(self):
        return self.__class__.__name__
class EvilRole(Role):
    evil = True
    def did_win(self,game:OneNight,player:ONP):
        return not game.sole_tanner_victory and not any(p.role.team==self.team and p.dead for p in game.players)
    @classmethod
    def set_valid(cls, rset: typing.List[typing.Type[Role]], final):
        return super().set_valid(rset, False) and (not final or len([r for r in rset if r.team == cls.team]) < (len(rset) - 3) // 2)
class Village(Role):
    team = "village"
    def did_win(self,game:OneNight,player:ONP):
        if game.sole_tanner_victory:
            return False
        if not any(p.role.evil for p in game.players):
            return not any(p.dead for p in game.players)
        else:
            return any(p.dead for p in game.players if p.role.evil)
class ONP(dib.BasePlayer):
    role=None
    dead = False
    start_role = None
    dayskip = False
    claim = None
    voted_for = None
    async def assign(self,role:Role):
        self.role=role
        self.start_role=role
        await self.dm(f"You are a {self.role.name}!\n{self.role.desc}")

SETS = ["werewolf","daybreak","darkside"]
class OneNight(dib.BaseGame):
    playerclass = ONP
    roles = None
    shameable = False
    name = "onenight"
    no_pump = False
    max_players = 20
    def __init__(self,ctx):
        super().__init__(ctx)
        self.center = {}
        self.history = []
    async def dayskip(self, p:ONP):
        if not p.dayskip:
            p.dayskip=True
            await self.send(f"{p.name} has requested a dayskip! ({len([p for p in self.players if p.dayskip])} votes so far)")
    async def claim(self,p:ONP,claim:str):
        p.claim=claim
        all_claims = '\n'.join(f"{p.name}: {p.claim}" for p in self.players if p.claim)
        await self.send(f"{p.name} has claimed {claim}!\nCurrent claims:\n{all_claims}")
    async def run(self,*modifiers):
        if not modifiers:
            modifiers=["all"]
        if modifiers[0]=="all":
            modifiers=SETS
        all_roles = []
        for m in modifiers:
            if m in SETS:
                all_roles.extend(importlib.import_module(f"onenight.{m}").roles)
        for _ in range(10000):
            roles = []
            for n in range(len(self.players)+3):
                rset = [r for r in all_roles if r.set_valid(roles+[r], n==len(self.players)+2)]
                if not rset:
                     break
                roles.append(random.choice(rset))
            else:
                if all(r.set_valid(roles, True) for r in roles) and any(issubclass(r, EvilRole) for r in roles):
                    self.roles=roles
                    break
            continue
        else:
            await self.send("Couldn't find a valid set of roles, terminating game :cry:")
            self.done=True
            return
        random.shuffle(self.roles)
        random.shuffle(self.players)
        self.roles = [r(None if n>=len(self.players) else self.players[n]) for n,r in enumerate(self.roles)]
        rview = self.roles[:]
        random.shuffle(rview)
        rview.sort(key=lambda r:r.name)
        await self.send(f"Game started with roles: {dib.smart_list([r.name for r in rview])}")
        await dib.gather([p.assign(self.roles[n]) for n,p in enumerate(self.players)])
        await self.send("NIGHT PHASE")
        rorder = defaultdict(list)
        for r in self.roles:
            for ph in r.phases:
                rorder[ph].append(r)
        for c in range(1,4):
            self.center[c]=self.roles[len(self.players)+c-1]
        for r in self.roles:
            await r.setup(self)
        await dib.gather([p.role.preload(self) for p in self.players])
        await self.send("PRELOAD PHASE ENDED")
        for t in sorted(rorder.keys()):
            for r in rorder[t]:
                if r.user:
                    await r.execute(self, t)
        await self.send("NIGHT PHASE OVER!")
        await self.send(f"Role order: {', '.join(r.name for r in sum(rorder.values(),[]))}")
        if not all(p.fake for p in self.players):
            timer = dib.TextTimer(10*60,self.channel)
            pseudos = [asyncio.create_task(self.run_pseudocommand(f)) for f in [self.dayskip, self.claim]]
            done, pending = await asyncio.wait([timer.run(),self.check_dayskip()],return_when=asyncio.FIRST_COMPLETED)
            for p in pending:
                p.cancel()
            for p in pseudos:
                p.cancel()
        await self.send("VOTING TIME!")
        votes = await dib.smart_gather([self.dm_tag(p,[op for op in self.players if op!=p]) for p in self.players],self.players)
        for p,v in votes.items():
            p.voted_for=v
        vfor = list(votes.values())
        totals = {p:vfor.count(p) for p in self.players}
        if all(t==1 for t in totals.values()):
            await self.send("Everyone got one vote, nobody dies!")
        else:
            mx = max(totals.values())
            died = []
            await self.send(f"{dib.smart_list([d.name for d in died])} got the most votes, and were subsequently lynched!")
            for p,t in totals.items():
                if t==mx:
                    died.append(p)
                    await self.kill(p)
        await self.send("FINAL ROLES:")
        await self.long_send([f"{p.name}: {p.role.name}" for p in self.players])
        await self.send("GAME HISTORY:")
        await self.long_send(self.history)
        await self.end_game([p for p in self.players if p.role.did_win(self,p)])
    async def kill(self,p:ONP):
        if not p.dead:
            p.dead = True
            await p.role.on_death(self,p)
            return True
    async def check_dayskip(self):
        while True:
            if len([p for p in self.players if p.dayskip])>=len(self.players)/2:
                return True
            await asyncio.sleep(1)

    def swap_roles(self,p1:typing.Union[int,ONP],p2:typing.Union[int,ONP]):
        one = self.center[p1] if isinstance(p1,int) else p1.role
        two = self.center[p2] if isinstance(p2,int) else p2.role
        if isinstance(p1,int):
            self.center[p1]=two
        else:
            p1.role=two
        if isinstance(p2,int):
            self.center[p2]=one
        else:
            p2.role=one
    def other_players(self,p:ONP)->typing.List[ONP]:
        return [op for op in self.players if op!=p]
    @property
    def sole_tanner_victory(self):
        tanners = [p for p in self.players if p.role.team=="tanner"]
        dead = [p for p in self.players if p.dead]
        return tanners and dead and all(p in tanners for p in dead)
