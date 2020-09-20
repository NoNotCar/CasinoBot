from __future__ import annotations

import discord

import pimg
import vector
import word_list
from vector import V2
import dib
import random

ldist={0:"*"*2,1:"e"*12+"ai"*9+"o"*8+"nrt"*6+"slu"*4,
       2:"d"*4+"g"*3,3:"bcmp"*2,4:"fhvwy"*2,5:"k",8:"jx",10:"qz"}
def coords_to_v(coords:str):
    return V2(word_list.alphabet.index(coords[0]),int(coords[1:])-1)
class Letter(object):
    imgs=pimg.strip("scrabble/letters.png")
    blanks=pimg.strip("scrabble/lettersnoscore.png")
    def __init__(self,letter:str,blank=False):
        self.letter=letter
        self.img=(self.blanks if blank else self.imgs)[word_list.alphabet.index(self.letter)]
        self.score=0 if blank else [s for s,l in ldist.items() if letter in l][0]
class BoardSquare(object):
    letter_multiplier=1
    word_multiplier=1
    img=pimg.load("scrabble/square.png")

class LetterMult(BoardSquare):
    imgs=pimg.strip("scrabble/lettermult.png")
    def __init__(self,x):
        self.letter_multiplier=x
        self.img=self.imgs[x-2]
class WordMult(BoardSquare):
    imgs = pimg.strip("scrabble/wordmult.png")
    def __init__(self, x):
        self.word_multiplier = x
        self.img = self.imgs[x - 2]
class WordError(Exception):
    def __init__(self,msg):
        super().__init__()
        self.msg=msg
class Board(object):
    def __init__(self,sz:vector.V2):
        self.size=sz
        self.squares={pos:BoardSquare() for pos in sz.iter_locs()}
        self.letters={}
    def add_special(self,off:V2,bsc,*args):
        for o in off.rots()+V2(off.x,-off.y).rots():
            self.squares[self.size//2+o]=bsc(*args)
    def copy(self)->Board:
        copy=Board(self.size)
        copy.squares=self.squares
        copy.letters=self.letters.copy()
        return copy
    def place_and_score(self,pos:V2,d:V2,word:str,blanks=()):
        placed=[]
        first_move=not self.letters
        adj=False
        for n,l in enumerate(word):
            tpos=pos+d*n
            if first_move and tpos==self.size//2:
                adj=True
            elif any(apos in self.letters and self.letters[apos] not in placed for apos in vector.iter_offsets(tpos)):
                adj=True
            if p:=self.letters.get(tpos,None):
                if p.letter!=l:
                    raise WordError("Trying to override letter: %s" % p.letter)
            elif not tpos.within(self.size):
                raise WordError("Word extends out of board")
            else:
                placed.append(Letter(l,n in blanks))
                self.letters[tpos]=placed[-1]
        if not adj:
            if first_move:
                raise WordError("The first move must cover the center square")
            else:
                raise WordError("Not adjacent to any existing tiles!")
        score=0
        for pos,l in self.letters.items():
            for v in [vector.down,vector.right]:
                if pos-v not in self.letters:
                    word=""
                    wscore=0
                    wmult=0
                    for n in range(self.size.x):
                        tpos=pos+v*n
                        if letter:=self.letters.get(tpos,None):
                            if letter in placed:
                                wmult=max(wmult,1)
                                wmult*=self.squares[tpos].word_multiplier
                            wscore+=letter.score*self.squares[tpos].letter_multiplier
                            word+=letter.letter
                        else:
                            break
                    if len(word)==1:
                        continue
                    if word in word_list.sowpods:
                        score+=wscore*wmult
                    else:
                        raise WordError("%s is not a valid word" % word.upper())
        return [l.letter for l in placed],score+50*(len(placed)==7)
    def render(self)->pimg.PImg:
        i=pimg.PImg.filled(self.size*16,(100,100,100))
        for pos,s in self.squares.items():
            i.blit(s.img,pos*16)
        for pos,l in self.letters.items():
            i.blit(l.img,pos*16)
        return i

class ScrabblePlayer(dib.BasePlayer):
    handmsg=None
    async def send_hand(self):
        content="YOUR TILES:\n"+"".join(dib.econv(l) for l in self.hand)
        if self.handmsg:
            await self.handmsg.edit(content=content)
        else:
            self.handmsg = await self.user.dm(content)

class Scrabble(dib.BaseGame):
    name="scrabble"
    min_players = 2
    max_players = 4
    playerclass = ScrabblePlayer
    async def run(self,*modifiers):
        board=Board(V2(15,15))
        board.add_special(V2(7,7),WordMult,3)
        board.add_special(V2(7,0),WordMult,3)
        for n in range(3,7):
            board.add_special(V2(n,n),WordMult,2)
        board.add_special(vector.zero,WordMult,2)
        for off in [V2(2,2),V2(6,2)]:
            board.add_special(off,LetterMult,3)
        for off in [V2(7,4),V2(4,0),V2(5,1),V2(1,1)]:
            board.add_special(off,LetterMult,2)
        bag=list("".join(ldist.values()))
        random.shuffle(self.players)
        random.shuffle(bag)
        turn=0
        bag_empty_msg=False
        while bag or all(p.hand for p in self.players):
            for p in self.players:
                while bag and len(p.hand)<7:
                    p.hand.append(bag.pop())
                if not (bag or bag_empty_msg):
                    await self.send("The bag is empty!")
                    bag_empty_msg=True
                await p.send_hand()
            img=board.render().xn(4).img
            img.save("scrabble.png")
            playing=self.players[turn]
            await self.channel.send("It's %s's turn!" % playing.name, file=discord.File("scrabble.png"))
            while True:
                move=await self.wait_for_text(playing,"Make a move (e.g. h8 down gherkin), discard tiles, or pass.",False)
                move=move.lower()
                msplit=move.split()
                if move=="pass":
                    break
                elif msplit[0]=="discard":
                    if len(msplit)!=2:
                        await self.send("Invalid discard - example: discard etofg")
                    elif not bag:
                        await self.send("The bag is empty - discarding wouldn't do anything!")
                    else:
                        old_hand = playing.hand.copy()
                        for l in msplit[1]:
                            if l in playing.hand:
                                playing.hand.remove(l)
                            else:
                                await self.send("You don't have a %s!" % l.upper())
                                playing.hand=old_hand
                                break
                        else:
                            bag.extend(list(msplit[1]))
                            random.shuffle(bag)
                            await self.send("Discard successful!")
                            break
                else:
                    try:
                        old_hand=playing.hand.copy()
                        coords,d,word=move.split()
                        coords=coords_to_v(coords)
                        d={"down":vector.down,"right":vector.right}[d]
                        try:
                            b=board.copy()
                            placed,score=b.place_and_score(coords,d,word,[n for n,l in enumerate(word) if l not in playing.hand])
                            for l in placed:
                                if l in playing.hand:
                                    playing.hand.remove(l)
                                elif "*" in playing.hand:
                                    playing.hand.remove("*")
                                else:
                                    playing.hand=old_hand
                                    raise WordError("You don't have those letters!")
                            else:
                                board=b
                                playing.points+=score
                                await self.send("Move successful: %s %s" % (word.upper(),score))
                                break
                        except WordError as e:
                            await self.send(e.msg)
                    except (ValueError,KeyError):
                        await self.send("Invalid move format!")
            turn+=1
            turn%=len(self.players)
            await self.show_scoreboard()
        await self.end_points()






