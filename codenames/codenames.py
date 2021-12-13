import dib
import word_list
import random
import pimg
import discord
from vector import V2
from PIL import ImageFont
MAX_WORD_LENGTH=9
codewords = [w for w in word_list.common if len(w)<=MAX_WORD_LENGTH and w!="pass"]
CARD_SIZE = V2(24,16)
BACK = (50,)*3
bigbas = ImageFont.truetype("fonts/bebas.ttf",20)
class CodeGrid(object):
    SCALE = 4
    word_cards = [pimg.load(f"codenames/word{n+1}.png") for n in range(5)]
    def __init__(self,size=V2(5,5)):
        self.size=size
        total_words = size.x*size.y
        self.RED_WORDS = total_words//3+1
        self.BLUE_WORDS = total_words//3
        self.words=random.sample(codewords,total_words)
        self.grid=[self.words[n*size.x:n*size.x+size.x] for n in range(size.y)]
        self.flipped=set()
        self.wcols={}
        temp_words=self.words.copy()
        random.shuffle(temp_words)
        for r in range(self.RED_WORDS):
            self.wcols[temp_words[r]]="RED"
        for b in range(self.BLUE_WORDS):
            self.wcols[temp_words[b+self.RED_WORDS]] = "BLUE"
        self.wcols[temp_words[self.RED_WORDS+self.BLUE_WORDS]]="ASSASSIN"
        for w in temp_words[self.RED_WORDS+self.BLUE_WORDS+1:]:
            self.wcols[w]="NEUTRAL"
    def word_card(self,word,pad=" "):
        pad_amount=MAX_WORD_LENGTH+2-len(word)
        left=pad_amount//2
        return "["+pad*left+word+pad*(pad_amount-left)+"]"
    def render_board(self,codemaster=False):
        paddict={"RED":"<","BLUE":">","ASSASSIN":"#","NEUTRAL":"-"}
        return "```%s```" % "\n".join("".join(
            self.word_card("" if word in self.flipped else word.upper(),paddict[self.wcols[word]] if codemaster or word in self.flipped else " ")
            for word in row) for row in self.grid)
    def render_img(self,codemaster=False):
        base = pimg.PImg.filled(CARD_SIZE*self.size,BACK)
        renderdict = {"RED":1,"BLUE":2,"NEUTRAL":3,"ASSASSIN":4}
        for y,row in enumerate(self.grid):
            for x,word in enumerate(row):
                n = renderdict[self.wcols[word]] if codemaster or word in self.flipped else 0
                base.blit(self.word_cards[n],V2(x,y)*CARD_SIZE)
        scaled = base.xn(self.SCALE)
        for y,row in enumerate(self.grid):
            for x,word in enumerate(row):
                if word not in self.flipped:
                    scaled.write(word,bigbas,V2(x,y)*CARD_SIZE*self.SCALE+CARD_SIZE*(self.SCALE*0.5))
        scaled.save("codenames/board.png")
    def is_valid_clue(self,submission):
        try:
            word, num = submission.split()
            if word.lower() not in word_list.words or word.lower() in self.leftover_words:
                return False
            return num.lower() == "inf" or 0 <= int(num) <= 9
        except ValueError:
            return False
    @property
    def leftover_words(self):
        return [w for w in self.words if w not in self.flipped]
    def team_won(self,team):
        return not any(self.wcols[w]==team for w in self.leftover_words)
class Codenames(dib.BaseGame):
    name = "codenames"
    team_names=["RED","BLUE"]
    min_players = 1
    max_players = 12
    grid=None
    async def run(self,*modifiers):
        self.grid=CodeGrid(V2(7,7) if "extreme" in modifiers else V2(5,5))
        await self.send("Speak now if you wish to become master of the codes.")
        left_master=await self.wait_for_shout("")
        await self.send("%s has volunteered for red codemaster" % left_master.name)
        right_master=await self.wait_for_shout("",[p for p in self.players if p!=left_master])
        remaining=[p for p in self.players if p not in (left_master,right_master)]
        random.shuffle(remaining)
        left_team=remaining[:len(remaining)//2]
        right_team=remaining[len(remaining)//2:]
        await self.send("Red team: %s; lead by %s.\nBlue team: %s; led by %s." %
                        (dib.smart_list([p.name for p in left_team]),left_master.name,dib.smart_list([p.name for p in right_team]),right_master.name))
        masters=[left_master,right_master]
        teams=[left_team,right_team]
        self.grid.render_img(True)
        await right_master.dm("THE BOARD:",file=discord.File("codenames/board.png"))
        turn=0
        while not self.done:
            self.grid.render_img()
            await self.send("Current Board:",file=discord.File("codenames/board.png"))
            await self.send("%s's codemaster is thinking of a clue..." % self.team_names[turn].capitalize())
            self.grid.render_img(True)
            await masters[turn].dm("Current Board:", file=discord.File("codenames/board.png"))
            clue = await self.wait_for_text(masters[turn],"Submit your clue!",True,self.grid.is_valid_clue)
            await self.send("THE CLUE: %s" % clue.upper())
            word,num=clue.lower().split()
            guesses=0
            while num=="0" or num=="inf" or guesses<=int(num):
                guesses+=1
                word=await self.choose_option(teams[turn],False,self.grid.leftover_words+["pass"],"Guessing time!" if guesses==1 else "The guessing continues...",True)
                if word=="pass":
                    break
                colour=self.grid.wcols[word]
                self.grid.flipped.add(word)
                if colour in self.team_names:
                    await self.send("%s was a %s team word!" % (word.upper(),colour))
                    if colour==self.team_names[turn] and not self.grid.team_won(self.team_names[turn]):
                        continue
                elif colour=="ASSASSIN":
                    await self.send("%s was the assassin! Bad luck!" % word.upper())
                    await self.end_game(teams[not turn]+[masters[not turn]])
                    return
                else:
                    await self.send("%s was neutral." % word.upper())
                break

            if self.grid.team_won("RED"):
                await self.send("RED TEAM WINS!")
                await self.end_game(left_team+[left_master])
            elif self.grid.team_won("BLUE"):
                await self.send("BLUE TEAM WINS!")
                await self.end_game(right_team+[right_master])
            await self.send("Guessing phase over!")
            turn=1-turn
    async def end_game(self,winners,losers=None,draw=False):
        self.grid.flipped.clear()
        self.grid.render_img(True)
        await self.send("FINAL BOARD:", file=discord.File("codenames/board.png"))
        await super().end_game(winners,losers,draw)







