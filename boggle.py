import dib
import word_list
import random
import vector
import asyncio
from vector import V2
around = vector.around+vector.ddirs
def get_score(length:int):
    m = max(length,4)-3
    return int(m*(m+1)/2)
class BoggleBoard(object):
    def __init__(self,size:V2):
        dist = word_list.ldist.copy()
        random.shuffle(dist)
        self.size=size
        self.board = dib.bidict()
        for v in size.iter_locs():
            self.board[v]=dist.pop()
    def find_recursively(self,substring:str,lpos:V2,used:tuple):
        if not substring:
            return True
        for a in around:
            tpos = lpos+a
            if tpos in self.board and self.board[tpos]==substring[0] and tpos not in used:
                if self.find_recursively(substring[1:],tpos,used+(tpos,)):
                    return True
        return False
    def spellable(self,word:str):
        if word not in word_list.sowpods or len(word)<3:
            return False
        if all(l in self.board.inverse for l in word):
            for src in self.board.inverse[word[0]]:
                if self.find_recursively(word[1:],src,(src,)):
                    return True
        return False
    def longest_possible(self):
        best = ""
        for w in word_list.sowpods:
            if len(w)>len(best) and self.spellable(w):
                best=w
        return best
    def print(self):
        return "\n".join("".join(dib.to_emoji(self.board[V2(x,y)]) for x in range(self.size.x)) for y in range(self.size.y))

class BogglePlayer(dib.BasePlayer):
    MAX_DM_LENGTH = 10
    words = None
    penalty = 0
    def __init__(self,user,fake=False):
        super().__init__(user,fake)
    async def submission_phase(self,game:dib.BaseGame,board:BoggleBoard,hardcore=False):
        trash = self.MAX_DM_LENGTH
        scoremsg = None
        self.words = set()
        while True:
            if trash>=self.MAX_DM_LENGTH:
                trash=0
                await self.dm(board.print())
                scoremsg = await self.dm(f"Current words: {len(self.words)}. Penalty points: {self.penalty}")
            m = await game.bot.wait_for("message",check=lambda m: m.channel == self.dmchannel and m.author == self.du and m.content)
            trash+=1
            word = m.content.lower()
            if board.spellable(word):
                self.words.add(word)
                await scoremsg.edit(content=f"Current words: {len(self.words)}. Penalty points: {self.penalty}")
            elif len(word)<3:
                await self.dm("not long enough...")
                if random.randint(0,1000)==999:
                    await self.dm("just like you lmao")
                trash+=1
            elif word in word_list.sowpods:
                await self.dm("not spellable...")
                trash+=1
            else:
                if hardcore:
                    await self.dm("You fool, that's an invalid word!")
                    self.penalty+=1
                else:
                    await self.dm("invalid word...")
                trash += 1
class Boggle(dib.BaseGame):
    name="boggle"
    min_players = 1
    max_players = 20
    playerclass = BogglePlayer
    rounds = 1
    no_pump = False
    async def run(self,*modifiers):
        if modifiers:
            try:
                self.rounds = max(1,int(modifiers[0]))
            except ValueError:
                pass
        hardcore = "hardcore" in modifiers
        if hardcore:
            await self.send(":warning: HARDCORE MODE ACTIVE :warning:")
        self.rewards=5*self.rounds
        for r in range(self.rounds):
            if self.rounds>1:
                await self.send(f"ROUND {r+1}/{self.rounds}")
            board = BoggleBoard(V2(4,4))
            await self.send("TWO MINUTES REMAIN!")
            await self.pump()
            try:
                await asyncio.wait_for(dib.gather([p.submission_phase(self,board,hardcore) for p in self.players]),120)
            except asyncio.TimeoutError:
                for p in self.players:
                    await p.dm("TIME'S UP FOLKS")
            for p in self.players:
                valid_words = [w for w in p.words if not any(w in op.words for op in self.players if op!=p)]
                score = sum(get_score(len(w)) for w in valid_words)-p.penalty
                await self.send("%s got %s/%s unique words, and gets %s points!\n%s" % (p.name,len(valid_words),len(p.words),score,", ".join(valid_words)))
                p.points+=score
                p.penalty=0
            await self.send("The best word anyone could have gotten was %s!" % board.longest_possible().upper())
            await self.show_scoreboard(r==self.rounds-1)
            if r!=self.rounds-1:
                await self.pump()
                await asyncio.sleep(20)
        await self.end_points()


