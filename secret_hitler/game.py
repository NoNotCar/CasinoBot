import discord
import dib
from discord.ext import commands
import random
import asyncio
import inspect
from . import roles, policies,events
task=asyncio.create_task
emoji_votes={"ja":":ok:","nein":":x:"}
track_cols={"liberal":":blue_circle:","fascist":":red_circle:"}
fascists={5:1,6:1,7:2,8:2,9:3,10:3}
def swap(l:list,tar,rep,k=1):
    for n,x in enumerate(l):
        if x==tar:
            l[n]=rep
            k-=1
            if not k:
                return l
ft56=[None,None,events.Peek(),events.Execute(),events.Execute(),None]
ft78=[None,events.Investigate(),events.SpecialElection(),events.Execute(),events.Execute(),None]
ft910=[events.Investigate(),events.Investigate(),events.SpecialElection(),events.Execute(),events.Execute(),None]
fts={5:ft56,6:ft56,7:ft78,8:ft78,9:ft910,10:ft910}
memos={"anarchy":"Game modifier: adds the shutdown, terrorism and corruption neutral policies to the deck",
       "intrigue":"Game modifier: adds the smear, forecast and audit neutral policies to the deck",
       "split":"Game modifier: liberal team splits into liberals and conservatives, with each trying to pass 3 of their 4 policies. Liberals win if Hitler is killed.",
       "farmyard":"Game modifier: a sheep replaces a liberal and a goat replaces a fascist",
       "suicide":"Game modifier: one of the fascists is replaced by a Tanner. There is also an extra execute event."}
for n,v in inspect.getmembers(roles):
    if inspect.isclass(v) and issubclass(v,roles.Liberal):
        memos[v.true_name.lower()]=v.help
for n,v in inspect.getmembers(policies):
    if inspect.isclass(v) and issubclass(v,policies.Policy) and v.memo:
        memos[v.name.lower()]=v.memo
memos["memos"]="Information is available for: "+", ".join(memos.keys())
class Track(object):
    progress=0
    def __init__(self,name,events):
        self.name=name
        self.events=events
    @property
    def done(self):
        return self.progress==len(self.events)
    @property
    def rendered(self):
        return "".join(track_cols.get(self.name,":purple_circle:") if n<self.progress else ":white_circle:" if not e else e.track_emoji for n,e in enumerate(self.events))
class Player(dib.BasePlayer):
    role=None
    dead=False
    last_government=False
class Game(dib.BaseGame):
    playerclass = Player
    fails=0
    president=0
    special_president=-1
    p_cache=None
    chancellor=None
    min_players = 5
    name="shitler"
    info=memos
    def __init__(self,ctx):
        super().__init__(ctx)
        self.events=[]
        self.policy_deck=[policies.Fascist]*11+[policies.Liberal]*6
        self.discards=[]
        self.tracks={}
        self.events=[]
        self.roles=[]
    async def run(self,*modifiers):
        libs = len(self.players) - fascists[len(self.players)] - 1
        if "split" in modifiers:
            cons = libs // 2
            self.roles = [roles.Hitler] + [roles.Fascist] * fascists[len(self.players)] + [roles.Liberal] * cons + [
                roles.Conservative] * (libs - cons)
            self.tracks["fascist"] = Track("fascist", fts[len(self.players)])
            self.tracks["liberal"] = Track("liberal", [None] * 3)
            self.tracks["conservative"] = Track("conservative", [None] * 3)
            self.policy_deck = [policies.Fascist] * 11 + [policies.Liberal] * 4 + [policies.Conservative] * 4
        else:
            self.roles = [roles.Hitler] + [roles.Fascist] * fascists[len(self.players)] + [roles.Liberal] * libs
            self.tracks["fascist"] = Track("fascist", fts[len(self.players)])
            self.tracks["liberal"] = Track("liberal", [None] * 5)
        if "anarchy" in modifiers:
            self.policy_deck.extend([policies.Corruption, policies.Shutdown, policies.Terrorism])
        if "intrigue" in modifiers:
            self.policy_deck.extend([policies.Audit, policies.Forecast, policies.Smear])
        if "farmyard" in modifiers:
            swap(self.roles, roles.Fascist, roles.Goat)
            swap(self.roles, roles.Liberal, roles.Sheep)
        if "suicide" in modifiers:
            swap(self.roles, roles.Fascist, roles.Tanner)
            self.tracks["fascist"].events[5] = events.Execute()
        self.started=True
        self.policy_deck=[p() for p in self.policy_deck]
        random.shuffle(self.players)
        random.shuffle(self.roles)
        random.shuffle(self.policy_deck)
        for n,p in enumerate(self.players):
            p.role=self.roles[n](p)
        await asyncio.gather(*[p.role.on_become() for p in self.players])
        await asyncio.gather(*[p.role.on_game_start(self) for p in self.players])
        while True:
            await self.print_board()
            await self.channel.send("President %s, pick another player to be your chancellor" % self.current_president.name)
            self.special_president=-1
            self.chancellor=await self.wait_for_tag(self.current_president,[p for p in self.living_players if p is not self.current_president and not p.last_government])
            if await self.vote_phase():
                if isinstance(self.chancellor.role,roles.Hitler) and self.tracks["fascist"].progress>=3:
                    await self.channel.send("You elected HITLER as CHANCELLOR, you fools!")
                    await self.win("fascist")
                    return
                selected=[self.policy_deck.pop() for _ in range(3)]
                await self.channel.send("The president is choosing a policy to discard...")
                discard=await self.smart_options(self.current_president,True,selected,lambda p:p.name,"Choose a policy to discard: ")
                selected.remove(discard)
                self.discards.append(discard)
                vetoed=False
                if self.tracks["fascist"].progress==5:
                    await self.chancellor.dm("Your policies are: "+", ".join(p.name for p in selected))
                    if await self.choose_option(self.chancellor,True,["yes","no"],"Do you want to veto these policies? ")=="yes":
                        if await self.choose_option(self.chancellor,True,["yes","no"],"President, do you agree with the veto? ")=="yes":
                            vetoed=True
                if vetoed:
                    await self.frustrate_populace()
                else:
                    for p in self.players:
                        p.last_government = False
                    if len(self.players)!=5:
                        self.current_president.last_government=True
                    self.chancellor.last_government=True
                    await self.channel.send("The chancellor is choosing a policy to enact...")
                    enacted=await self.smart_options(self.chancellor,True,selected,lambda p:p.name,"Choose a policy to enact: ")
                    self.discards.append(next(p for p in selected if p is not enacted))
                    await self.enact(self.chancellor.name,enacted)
            else:
                await self.frustrate_populace()
            self.p_cache=None
            if self.special_president<0:
                self.president+=1
                self.president%=len(self.players)
                while self.current_president.dead:
                    self.p_cache=None
                    self.president+=1
                    self.president %= len(self.players)
            if self.done:
                break
    async def frustrate_populace(self):
        self.fails += 1
        if self.fails == 3:
            await self.channel.send("The populace are FRUSTRATED!")
            await self.enact("A frustrated populace", self.policy_deck.pop(), False)
    async def enact(self,enactor,policy,run_events=True):
        await self.channel.send("%s enacted a %s policy" % (enactor, policy.name.lower()))
        if len(self.policy_deck) < 3:
            self.policy_deck.extend(self.discards)
            self.discards = []
            random.shuffle(self.policy_deck)
            await self.channel.send("Deck fell below 3 cards, reshuffling...")
        if policy.track:
            ct = self.tracks[policy.track]
            if ct.events[ct.progress]:
                self.events.append(ct.events[ct.progress])
            ct.progress += 1
        if run_events:
            await policy.enact(self)
            while self.events and not self.done:
                await self.events.pop().do(self)
        else:
            self.events=[]
        for t in self.tracks.values():
            if t.done:
                await self.win(t.name)
        self.fails = 0
    async def print_board(self):
        await self.channel.send("\n".join("%s: %s" % (t.name.upper(),t.rendered) for t in self.tracks.values()))
        await self.channel.send(" | ".join(self.get_p_name_order(p) for n,p in enumerate(self.players)))
        await self.channel.send("Cards left in deck: %s" % len(self.policy_deck))
        await self.channel.send("Current rejects: %s/3" % self.fails)
    async def vote_phase(self):
        await self.channel.send("VOTING TIME!")
        for p in self.living_players:
            await task(p.dm("Time to vote! Voting options: "+" ,".join('"%s"' % o for o in p.role.vote_options)))
        votes=await asyncio.gather(*[self.wait_for_vote(p) for p in self.living_players])
        votes={p:v for p,v in votes}
        for p,v in votes.items():
            if v=="sheep":
                votes[p]=random.choice([ov for ov in votes.values() if ov!="sheep"])
        if "veto" in votes.values():
            await self.channel.send("Arthur has vetoed the mission!")
        else:
            await self.channel.send("------------------------------------------")
            await self.channel.send("\n".join("%s voted %s %s" % (p.name,v,emoji_votes.get(v,":question:")) for p,v in votes.items()))
        if self.is_approved(list(votes.values())):
            return True
        return False
    def is_approved(self,votes):
        if "veto" in votes:
            return False
        else:
            return votes.count("ja")>votes.count("nein")
    async def kill(self,target):
        target.dead = True
        await target.role.on_death(self)
        if not self.done:
            await self.channel.send("can we have an :regional_indicator_f: in the chat for %s" % target.name)
    async def wait_for_vote(self,player):
        if player.fake:
            return player,random.choice(player.role.vote_options)
        while True:
            m = await self.bot.wait_for("message",check=lambda m: isinstance(m.channel, discord.DMChannel) and m.author == player.du)
            v = await player.role.can_vote(m.content)
            if v:
                await player.dm("Vote successful!")
                await self.channel.send("%s has voted!" % player.name)
                return player,v
    def get_p_name_order(self,player):
        name=player.name
        idx=self.players.index(player)
        if player.dead:
            name+=" :skull:"
            return name
        if player is self.current_president:
            name+=" :man_office_worker:"
        if player.last_government:
            name+=" :zombie:"
        if idx==(self.president+(2-self.fails))%len(self.players):
            name+=" :man_judge:"
        return name
    async def win(self,winning_team):
        await self.channel.send("The %s team has won!" % winning_team)
        await self.channel.send("The roles:\n"+"\n".join("%s: %s" % (p.name,p.role.name) for p in self.players))
        await self.end_game([p for p in self.players if p.role.did_win(self,winning_team)],[p for p in self.players if not p.role.did_win(self,winning_team)],False)
        self.done=True
    @property
    def living_players(self):
        return [p for p in self.players if not p.dead]
    @property
    def current_president(self):
        if self.p_cache:
            return self.p_cache
        else:
            self.p_cache=self.players[self.special_president if self.special_president>=0 else self.president]
            return self.p_cache

