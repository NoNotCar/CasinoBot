import random
import asyncio

import discord

import dib
from .Roles import *
default_roles={5:[Evil, Morgana, Merlin, Percival, NeutGood],
               6:[Evil, Morgana, Merlin, Percival, NeutGood,NeutGood],
               7:[Morgana,Mordred,Oberon,Merlin,Percival,NeutGood,NeutGood],
               8:[Morgana,Mordred,Oberon,Merlin,Percival,NeutGood,NeutGood,NeutGood],
               9:[Morgana,Mordred,Evil,Merlin,Percival,NeutGood,NeutGood,NeutGood,NeutGood],
               10:[Morgana,Mordred,Oberon,Evil,Merlin,Percival,NeutGood,NeutGood,NeutGood,NeutGood],
               11:[Morgana,Mordred,Oberon,Evil,Evil,Merlin,Percival,NeutGood,NeutGood,NeutGood,NeutGood]}
mission_counts={5:[2,3,2,3,3],
                6:[2,3,4,3,4],
                7:[2,3,3,4,4],
                8:[3,4,4,5,5],
                9:[3,4,4,5,5],
                10:[3,4,4,5,5],
                11:[3,4,4,5,5]}
emoji_nums=[":zero:",":one:",":two:",":three:",":four:",":five:"]
emoji_votes={"approve":":ok:","reject":":x:"}
task = asyncio.create_task
normal_roles=[r for r in all_roles if r in default_roles[10]]
class Player(dib.BasePlayer):
    role=None
    _lady=False
    has_been_lady=False
    async def set_role(self,roleclass):
        self.role=roleclass(self)
        await self.role.on_become()
    @property
    def lady(self):
        return self._lady
    @lady.setter
    def lady(self,value):
        self._lady=value
        if value:
            self.has_been_lady=True
class Game(dib.BaseGame):
    name = "avalon"
    rounds=5
    roles=None
    cround=0
    king_pos=0
    fails=0
    winners=0
    murdered=None
    results=None
    pdict=None
    past_missions=None
    seed=None
    playerclass = Player
    min_players = 5
    max_players = 10
    info = {rn.lower():"\n".join([r(None).name,r.help]) for rn,r in rdict.items()}
    async def run(self,*modifiers):
        self.results=[]
        self.pdict={}
        self.past_missions=[]
        self.seed=random.getstate()
        roles=modifiers[0] if modifiers else None
        rset = modifiers[1] if len(modifiers)>1 else None
        if roles:
            if roles not in presets:
                await self.send("Not a valid preset! Valid presets: %s. Continuing with default roles..." % ", ".join(presets.keys()))
            else:
                for _ in range(10000):
                    test_roles=presets[roles][:]+[Merlin]
                    for _ in range(len(self.players)-len(test_roles)):
                        test_roles.append(random.choice([r for r in (normal_roles if rset=="normal" else all_roles)]))
                    if len([r for r in test_roles if r.evil])!=len([r for r in default_roles[len(self.players)] if r.evil]):
                        print("FAILED - INSUFFICIENT EVIL")
                        continue
                    if all(r.random_valid([r for n,r in enumerate(test_roles) if n!=m]) for m,r in enumerate(test_roles)):
                        self.roles = test_roles
                        break
                    print("FAILED - ROLES")
                else:
                    await self.send("Couldn't find a valid set of roles for that preset...")
        if not self.roles:
            self.roles=list(default_roles[len(self.players)])
        random.shuffle(self.roles)
        random.shuffle(self.players)
        for n,p in enumerate(self.players):
            await p.set_role(self.roles[n])
        for p in self.players:
            task(p.role.on_game_start(self))
        await self.send("The game has started! Current Roles:")
        await self.send(", ".join(p.role.name for p in self.players))
        self.info["avalon roles"] = "Current Roles: "+", ".join(p.role.name for p in self.players)
        random.shuffle(self.players)
        self.players[-1].lady=True
        await self.new_round()
    async def print_board(self):
        await self.channel.send("".join(":white_circle:" if n+1>=self.cround else ":blue_circle:" if self.results[n] else ":red_circle:" for n in range(5))+"\n"+
                                "".join(emoji_nums[mission_counts[len(self.players)][n]] for n in range(5)))
        await self.channel.send(" | ".join(self.get_p_name_order(p) for n,p in enumerate(self.players)))
        await self.channel.send("Current rejects: %s" % self.fails)
    async def new_round(self):
        self.cround+=1
        self.fails=0
        for p in self.players:
            await task(p.role.on_round_start(self))
        await self.channel.send("ROUND %s: %s on mission, %s fails required" %
        (self.cround,self.mission_size,self.fails_required(self.cround)))
        await self.print_board()
        if self.cround>2:
            await self.lady_time()
        while True:
            await self.send("%s, choose your mission!" % self.king.tag)
            mission=await self.wait_for_multitag(self.king,self.players,self.mission_size-1,self.mission_size)
            if len(mission) == self.mission_size - 1:
                if self.king in mission:
                    await self.send("Wrong number of people for this mission!")
                    continue
                else:
                    mission.append(self.king)
            if await self.voting_phase(mission):
                break
    async def lady_time(self):
        await self.channel.send("IT'S LADY TIME!")
        lady = next(p for p in self.players if p.lady)
        await self.send("Lady %s, choose someone to investigate!" % lady.name)
        target = await self.wait_for_tag(lady, [p for p in self.players if not p.has_been_lady])
        await self.send("Ladying %s..." % target.name)
        target.lady = True
        lady.lady = False
        await lady.dm("Target's allegiance is %s!" % ("evil" if target.role.lady_evil else "good"))
        for p in self.players:
            if isinstance(p.role, Lady):
                await p.dm("Target's allegiance was %s." % ("evil" if target.role.lady_evil else "good"))
    def fails_required(self,mission):
        return 2 if len(self.players)>6 and mission==4 else 1
    def get_p_name_order(self,player):
        name=player.name
        idx=self.players.index(player)
        if idx==self.king_pos:
            name+=" :crown:"
        if idx==(self.king_pos+(4-self.fails))%len(self.players):
            name+=" :man_judge:"
        if player.lady:
            name+=" :dancer:"
        return name
    async def wait_for_vote(self,player):
        while True:
            m = await self.wait_for_text(player,"Time to vote! Voting options: "+" ,".join('"%s"' % o for o in player.role.vote_options),faked=random.choice(player.role.vote_options))
            v = await player.role.can_vote(m)
            if v:
                await player.dm("Vote successful!")
                await self.channel.send("%s has voted!" % player.name)
                return player,v
    async def voting_phase(self,party):
        self.king_pos += 1
        self.king_pos %= len(self.players)
        if self.fails==4:
            await self.channel.send("The party: %s. Dictator round, no voting!" % ", ".join(p.name for p in party))
            await self.mission_phase(party)
            return True
        await self.channel.send("Suggested party: %s. VOTING TIME!" % ", ".join(p.name for p in party))
        votes=await asyncio.gather(*[self.wait_for_vote(p) for p in self.players])
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
            await self.channel.send("The mission proceeds...")
            await self.mission_phase(party)
            return True
        else:
            await self.channel.send("The mission was rejected. The crown moves on")
            self.fails+=1
            await self.print_board()
            return False
    async def wait_for_action(self,player):
        while True:
            m=await self.wait_for_text(player,"Time to quest! Mission options: "+" ,".join('"%s"' % o for o in player.role.mission_options),faked=random.choice(player.role.mission_options))
            action=await player.role.can_action(m)
            if action:
                await player.dm("Contribution successful!")
                await self.channel.send("%s has done their part!" % player.name)
                return action
    async def mission_phase(self,party):
        for p in party:
            await task(p.dm("Time to quest! Mission options: "+" ,".join('"%s"' % o for o in p.role.mission_options)))
        result=await asyncio.gather(*[self.wait_for_action(p) for p in party])
        random.shuffle(result)
        self.past_missions.append((party,result))
        await self.channel.send("Mission Results: "+", ".join(result))
        if "bomb" in result:
            terrorist=[p for p in self.players if isinstance(p.role,Terrorist)][0]
            await self.channel.send("A bomb explodes, killing everyone! The terrorist, %s, wins!" % terrorist.name)
            await self.final_message(False,False)
            return
        success=self.is_successful(result)
        await self.channel.send("The mission %s!" % ("succeeded" if success else "failed"))
        self.results.append(success)
        if self.results.count(1)==3:
            await self.game_end(False)
        elif self.results.count(0)==3:
            await self.game_end(True)
        else:
            self.info["past missions"]=self.previous_missions
            await self.new_round()
    async def game_end(self,evil_wins):
        self.done=True
        if Merlin in self.roles:
            if evil_wins:
                await self.channel.send("The quests have failed. Evil has won, but can try and kill Merlin for fun :smiling_imp:")
            else:
                await self.channel.send("Good has succeeded in their quest, but has Merlin remained secret?")
            valid_assassins = [p for p in self.players if p.role.evil and p.role.known_to_evil]
            assassin = random.choice(valid_assassins)
            await self.send("%s, you have been selected as THE ASSASSIN. Choose someone to kill!" % assassin.tag)
            self.murdered = await self.wait_for_tag(assassin,[p for p in self.players if not p.role.known_to_evil])
            await self.send("Assassinating %s..." % self.murdered.name)
            await self.final_message(evil_wins or isinstance(self.murdered.role, Merlin))
        else:
            await self.final_message(evil_wins)
    async def final_message(self,evil_wins,special=False):
        if special:
            pass
        elif evil_wins:
            await self.channel.send("Evil has once again fallen over the land...")
        else:
            await self.channel.send("Good has succeeded in their quest!")
        await self.channel.send("The roles:\n"+"\n".join("%s: %s" % (p.name,p.role.name) for p in self.players))
        if not special:
            await self.channel.send("(%s won)" % ", ".join(p.name for p in self.players if p.role.did_win(self,evil_wins)))
        await self.end_game([p for p in self.players if p.role.did_win(self,evil_wins)])
    def is_approved(self,votes):
        if "veto" in votes:
            return False
        else:
            return votes.count("approve")>votes.count("reject")
    def is_successful(self,result):
        reversals=result.count("reverse")
        return bool(result.count("fail")<self.fails_required(self.cround))!=reversals%2
    @property
    def mission_size(self):
        return mission_counts[len(self.players)][self.cround-1]
    @property
    def king(self):
        return self.players[self.king_pos]
    @property
    def previous_missions(self):
        to_print = "PREVIOUS MISSIONS:"
        for n, (party, result) in enumerate(self.past_missions):
            to_print += "\nMISSION %s:\n" % (n + 1)
            to_print += "Party: " + ", ".join(p.name for p in party) + "\n"
            to_print += "Result: " + ", ".join(result)
        return to_print

