import dib
import asyncio
import random

locations = {"Theater":":performing_arts:","Restaurant":":fork_knife_plate:","Beach":":beach:",
"School":":school_satchel:","Supermarket":":apple:","Service Station":":blue_car:",
"Circus":":circus_tent:","Hospital":":hospital:","Crusader Army":":cross:","Train":":train2:","Bank":":moneybag:",
             "Airplane":":airplane:","Police Station":":cop:","Pirate Ship":":pirate_flag:","Movie Studio":":movie_camera:",
             "Army Base":":military_helmet:","Submarine":":ocean:","Cruise Ship":":cruise_ship:","Polar Station":":penguin:",
             "Love Hotel":":love_hotel:","Corporate Party":":bar_chart:","Day Spa":":nail_care:","University":":student:",
             "Embassy":":flag_gb:","Space Station":":astronaut:","Casino":":game_die:","Cathedral":":church:"}
def emojified(l:str):
    return f"{l}: {locations[l]}"
class Agent(dib.BasePlayer):
    done = False
    vote = True
    guess = None
    async def spy_phase(self,game:dib.BaseGame,subset:list):
        self.guess = await game.choose_option(self,True,subset,"You may guess a location at any point. Available locations:\n"+"\n".join(emojified(s) for s in subset),True)
        return self.guess



class Spyfall(dib.BaseGame):
    name="spyfall"
    min_players = 3
    max_players = 20
    MULT = 8
    SUBSET = 20
    ROUNDS = 5
    shameable = False
    playerclass = Agent
    async def run(self,*modifiers):
        subset = random.sample(locations.keys(),self.SUBSET)
        for n in range(self.ROUNDS):
            await self.send(f"Round {n+1}/{self.ROUNDS}")
            spies = random.sample(self.players,1+len(self.players)//self.MULT)
            for p in self.players:
                p.done = False
                p.vote = True
                p.guess = None
            normies = [p for p in self.players if p not in spies]
            location = random.choice(subset)
            for n in normies:
                await n.dm(f"You are in the {emojified(location)}! Find the spy!")
            for s in spies:
                await s.dm("You are a spy! Find out the location before you're found out!")
            first = random.choice(self.players)
            await self.send("Anyone can accuse someone by tagging them in this chat.\n%s, you're asking the first question!" % first.tag)
            timer = dib.TextTimer(8*60,self.channel)
            while not all(s.done for s in spies) and any(n.vote for n in normies):
                undone = [p for p in self.players if not p.done]
                can_call_votes = [p for p in undone if p.vote]
                done,pending = await asyncio.wait([s.spy_phase(self,subset) for s in spies if not s.done]+[timer.run(),self.wait_for_tag(can_call_votes,undone)],
                                                  return_when=asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()
                if timer.done:
                    await self.send("TIME'S UP! All surviving spies (%s) get points!" % dib.smart_list([s.name for s in spies]))
                    for s in spies:
                        if not s.done:
                            s.points+=1
                    break
                else:
                    for d in done:
                        res = d.result()
                        if isinstance(res,Agent):
                            self.dunnit.vote = False
                            await self.send(f"{self.dunnit.name} has accused {res.name} of being a spy!")
                            votes = await dib.gather([self.choose_option(p,True,["yes","no"],f"Is {res.name} a spy?",True) for p in undone if p not in spies and p!=res])
                            successful = all(v=="yes" for v in votes)
                            if successful:
                                await self.send("The vote was successful!")
                                if res in spies:
                                    await self.send(f"{res.name} was a spy!")
                                    res.done=True
                                    for n in normies:
                                        n.points+=1
                                else:
                                    await self.send(f"Oh no! {res.name} wasn't a spy! You idiots!")
                                    for s in spies:
                                        s.points+=1
                                        s.done=True
                            else:
                                await self.send("The vote wasn't successful. The game continues...")
                        else:
                            for s in spies:
                                if s.guess and not s.done:
                                    s.done = True
                                    if s.guess==location:
                                        await self.send(f"{s.name} was a spy, and guessed the location correctly!")
                                        s.points+=1
                                    else:
                                        await self.send(f"{s.name} was a spy, and got the location wrong!")
                                        s.points-=1
            await self.send(f"(The location was {location})")
            await self.show_scoreboard(n==self.ROUNDS-1)
        await self.end_points()


