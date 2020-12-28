import dib
from .roles import *
import random
MAFIA_FRACTION = 0.32
class MafiaPlayer(dib.BasePlayer):
    role=None
    dead=False
    attacked=False
    healed=False
    async def set_role(self,roleclass):
        self.role=roleclass(self)
        await self.role.on_become()
    @property
    def evil(self):
        return self.role.evil
class Mafia(dib.BaseGame):
    playerclass = MafiaPlayer
    min_players = 5
    max_players = 20
    roles=None
    name="mafia"
    async def run(self,*modifiers):
        for _ in range(10000):
            roles = []
            for n in range(len(self.players)):
                rset = [r for r in (goods if n+1>len(self.players)*MAFIA_FRACTION else evils) if r.random_valid(roles)]
                if not rset:
                     break
                roles.append(random.choice(rset))
            else:
                if all(r.random_valid([r for n, r in enumerate(roles) if n != m]) for m, r in enumerate(roles)):
                    self.roles=roles
                    break
            continue
        else:
            await self.send("Couldn't find a valid set of roles, terminating game :cry:")
            return
        random.shuffle(self.players)
        random.shuffle(self.roles)
        await dib.gather([p.set_role(self.roles[n]) for n,p in enumerate(self.players)])
        await dib.gather([p.role.on_game_start(self) for p in self.players])
        await self.send("The game has started! Current Roles:\n"+", ".join(p.role.name for p in self.players))
        random.shuffle(self.players)
        while not self.done:
            await self.night_phase()
            await self.check_game_over()
            if not self.done:
                await self.day_phase()
                await self.check_game_over()
    async def night_phase(self):
        await self.send("The night phase has begun! No talking!")
        phases = set(sum((p.role.night_phases for p in self.alive),[]))
        for ph in sorted(phases):
            await dib.gather([p.role.night_phase(self,ph) for p in self.alive if ph in p.role.night_phases])
        dead = [p for p in self.alive if p.attacked and await p.role.on_attack(self)]
        if dead:
            for p in dead:
                await p.dm("You died! Join the death chat or something.")
                p.dead=True
            await self.send("As the sun rises, you find %s brutally murdered in their sleep." % dib.smart_list([p.name for p in dead]))
        else:
            await self.send("As the sun rises, you find that on this one night, nobody died!")
        for p in self.alive:
            p.attacked=False
            p.healed=False
    async def day_phase(self):
        await self.send("It's now daytime! Discuss the events of the night, and once a majority of people call for a vote the voting will begin!")
        skip_voters=[p for p in self.alive if p.fake]
        while len(skip_voters)/len(self.alive)<0.5:
            skipper=await self.wait_for_shout("",[p for p in self.alive if p not in skip_voters])
            skip_voters.append(skipper)
            await self.send("%s has called for a vote! (%s total)" % (skipper.name,len(skip_voters)))
        await self.send("VOTING TIME! Choose someone to kill!")
        votes = await dib.gather([self.dm_tag(p,[o for o in self.alive if o is not p],True) for p in self.alive])
        counts = {v:votes.count(v) for v in votes}
        await self.send("Vote totals:\n"+"\n".join("%s: %s" % (v.name if v else "Nobody",c) for v,c in counts.items()))
        if list(counts.values()).count(max(counts.values()))>1:
            await self.send("The vote is tied! Nobody dies!")
        else:
            mx = max(counts.values())
            dying = next(v for v,c in counts.items() if c==mx)
            if dying:
                await self.send("%s has been executed!" % dying.name)
                await self.kill(dying)
            else:
                await self.send("Nobody dies today!")
    async def kill(self,p):
        await p.role.on_death(self)
        await p.dm("You died! Join the death chat or something.")
        p.dead = True
    async def check_game_over(self):
        if not self.alive:
            await self.send("The population of the village has reached 0. GAME OVER!")
            await self.game_over(False)
        elif not any(p.evil for p in self.alive):
            await self.send("It seems like the mafia are gone from the village!")
            await self.game_over(False)
        elif len([p for p in self.alive if p.evil])/len(self.alive)>=0.5:
            await self.send("The mafia have reached a majority, and have taken over the village!")
            await self.game_over(True)
    async def game_over(self, evil_wins):
        await dib.gather([p.role.cleanup(self) for p in self.players])
        await self.channel.send("The roles:\n" + "\n".join("%s: %s" % (p.name, p.role.name) for p in self.players))
        await self.channel.send(
            "(%s won)" % ", ".join(p.name for p in self.players if p.role.did_win(self, evil_wins)))
        await self.end_game([p for p in self.players if p.role.did_win(self, evil_wins)])
    @property
    def alive(self):
        return [p for p in self.players if not p.dead]
