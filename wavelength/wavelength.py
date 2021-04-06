import dib
import random

resolution = 20
opposites=[]
with open("wavelength/opposites.txt","r") as f:
    for w in f.readlines():
        if w:
            opposites.append(w.strip())

class Wavelength(dib.BaseGame):
    min_players = 4
    max_players = 20
    teams = [":gem:",":ribbon:"]
    name="wavelength"
    async def run(self,*modifiers):
        random.shuffle(self.players)
        team1 = self.players[::2]
        team2 = self.players[1::2]
        points = [0,1]
        await self.send(f"Team {self.teams[0]}: {dib.smart_list([p.name for p in team1])}\nTeam {self.teams[1]}: {dib.smart_list([p.name for p in team2])}")
        tt=0
        turn=0
        opps = opposites.copy()
        random.shuffle(opps)
        while all(p<10 for p in points):
            opp = opps.pop()
            team = team2 if tt else team1
            other_team = team1 if tt else team2
            cluegiver = team[turn%len(team)]
            guessers = [p for p in team if p!=cluegiver]
            await self.send(f"Team {self.teams[tt]}'s turn.\nAxis: {opp.upper()}.\nCurrent points: {self.teams[0]}:{points[0]}, {self.teams[1]}:{points[1]}.\n{cluegiver.name} is thinking of a clue...")
            amount = random.randint(1,resolution)
            clue = await self.wait_for_text(cluegiver,f"Give a clue that is {amount}/{resolution} along the axis {opp.upper()}!")
            guess=await self.choose_number(guessers,False,1,resolution,f"{cluegiver.name} gave the clue {clue}. Guess the position! (1-{resolution})")
            if guess==amount:
                await self.send(f"Team {self.teams[tt]} got it bang on! They get 4 points!")
                points[tt]+=4
            else:
                hl = await self.choose_option(other_team,False,["higher","lower"],f"Team {self.teams[1-tt]}, is the true answer **higher** or **lower**?",True)
                if (hl=="higher")==(amount>guess):
                    await self.send("CORRECT! You get 1 point!")
                    points[1-tt]+=1
                winnings = max(0,4-abs(amount-guess))
                await self.send(f"The true answer was {amount}, so team {self.teams[tt]} get {winnings} points.")
            if tt:
                turn += 1
            tt=1-tt
        if points[1]>points[0]:
            await self.send(f"Team {self.teams[1]} won!")
            await self.end_game(team2,team1)
        elif points[0]>points[1]:
            await self.send(f"Team {self.teams[0]} won!")
            await self.end_game(team1, team2)
        else:
            await self.send(f"It's a draw!")
            await self.end_game(self.players)


