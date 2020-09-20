import dib
import word_list
import random
MAX_WORD_LENGTH=7
codewords = [w for w in word_list.common if len(w)<=MAX_WORD_LENGTH and w!="pass"]


class CodeGrid(object):
    RED_WORDS=9
    BLUE_WORDS=8
    def __init__(self):
        self.words=random.sample(codewords,25)
        self.grid=[self.words[n*5:n*5+5] for n in range(5)]
        self.flipped=set()
        self.wcols={}
        temp_words=self.words.copy()
        random.shuffle(temp_words)
        for r in range(self.RED_WORDS):
            self.wcols[temp_words[r]]="LEFT"
        for b in range(self.BLUE_WORDS):
            self.wcols[temp_words[b+self.RED_WORDS]] = "RIGHT"
        self.wcols[temp_words[self.RED_WORDS+self.BLUE_WORDS]]="ASSASSIN"
        for w in temp_words[self.RED_WORDS+self.BLUE_WORDS+1:]:
            self.wcols[w]="NEUTRAL"
    def word_card(self,word,pad=" "):
        pad_amount=MAX_WORD_LENGTH+2-len(word)
        left=pad_amount//2
        return "["+pad*left+word+pad*(pad_amount-left)+"]"
    def render_board(self,codemaster=False):
        paddict={"LEFT":"<","RIGHT":">","ASSASSIN":"#","NEUTRAL":"-"}
        return "```%s```" % "\n".join("".join(
            self.word_card("" if word in self.flipped else word.upper(),paddict[self.wcols[word]] if codemaster or word in self.flipped else " ")
            for word in row) for row in self.grid)
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
    team_names=["LEFT","RIGHT"]
    min_players = 1
    max_players = 12
    grid=None
    async def run(self,*modifiers):
        self.grid=CodeGrid()
        await self.send("Speak now if you wish to become master of the codes.")
        left_master=await self.wait_for_shout("")
        await self.send("%s has volunteered for left codemaster" % left_master.name)
        right_master=await self.wait_for_shout("",[p for p in self.players if p!=left_master])
        remaining=[p for p in self.players if p not in (left_master,right_master)]
        random.shuffle(remaining)
        left_team=remaining[:len(remaining)//2]
        right_team=remaining[len(remaining)//2:]
        await self.send("Left team: %s; lead by %s.\nRight team: %s; lead by %s." %
                        (dib.smart_list([p.name for p in left_team]),left_master.name,dib.smart_list([p.name for p in right_team]),right_master.name))
        masters=[left_master,right_master]
        teams=[left_team,right_team]
        await right_master.dm(self.grid.render_board(True))
        turn=0
        while not self.done:
            await self.send("Current Board:\n"+self.grid.render_board())
            await self.send("%s's codemaster is thinking of a clue..." % self.team_names[turn].capitalize())
            clue = await self.wait_for_text(masters[turn],"Current Board:\n%s\nSubmit your clue!" % self.grid.render_board(True),True,self.grid.is_valid_clue)
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

            if self.grid.team_won("LEFT"):
                await self.send("LEFT TEAM WINS!")
                await self.end_game(left_team+[left_master])
            elif self.grid.team_won("RIGHT"):
                await self.send("RIGHT TEAM WINS!")
                await self.end_game(right_team+[right_master])
            await self.send("Guessing phase over!")
            turn=1-turn
    async def end_game(self,winners,losers=None,draw=False):
        self.grid.flipped.clear()
        await self.send("FINAL GRID\n"+self.grid.render_board(True))
        await super().end_game(winners,losers,draw)







