from . import Board
from . import Pieces
from random import choice
import textwrap
import datetime
from . import PImg, Vector, Colour
from PIL import Image, ImageDraw
from .Vector import Vector2 as V
lfont= PImg.fload("cool", 96)
itfont=PImg.fload("cool", 64)
tfont= PImg.fload("cool", 32)
ifont=PImg.fload("cool", 24)
T_COL=(0,0,0,50)
numbers=[PImg.colcopy(i, (19,) * 3, T_COL) for i in PImg.imgstripx("numbers", 8)]
letters=[PImg.colcopy(i, (19,) * 3, T_COL) for i in PImg.imgstripx("letters", 8)]
K_SELECT=0.2
class Match(object):
    turn=0
    turns=-1
    done=False
    last_move_time=None
    draw_offer=False
    def __init__(self,competitors,bs):
        ps = [choice(x) for x in [Pieces.forts, Pieces.shock,Pieces.guards, Pieces.titans]]
        self.b=Board.Board(bs, ps)
        self.comps=competitors
        self.switch_turn()
    def render(self,scale):
        rs=(scale+1)*16
        ss=Image.new("RGBA",((self.b.size+Vector.down)*rs).tuple,(100,100,100))
        offset=Vector.down*(rs//2)
        PImg.bcentrex(tfont, self.comps[0].name, ss, -12, self.comps[0].col)
        PImg.bcentrex(tfont, self.comps[1].name, ss, ss.height - 44, self.comps[1].col)
        draw=ImageDraw.Draw(ss)
        for v in self.b.size.iter_locs():
            draw.rectangle(((v*rs+offset).tuple,(v*rs+offset+Vector.one*rs).tuple),self.b.theme[(v.x + v.y) % 2])
            PImg.blit(letters[v.x][scale],ss,v*rs+offset)
            PImg.blit(numbers[v.y][scale],ss,v*rs+offset+V(rs//2,0))
        for pos,piece in self.b.board.items():
            if piece:
                PImg.blit(Pieces.pimgs[piece.name][self.comps[piece.side].col][piece.flips and not piece.side][scale],ss,(pos*rs+offset))
        return ss
    def switch_turn(self):
        if self.b.lost[self.turn]:
            self.lose()
        self.turn=not self.turn
        self.turns+=1
        self.possmoves=[]
        self.last_move_time=datetime.datetime.now()
        if not self.done and self.b.lost[self.turn]:
            self.lose()
    def on_move(self,p1,p2):
        if not self.b[p1] or self.b[p1].side!=self.turn:
            return False
        try:
            sel_move=[m for m in self.b.get_moves(self.b[p1],p1) if m.v==(p2-p1)][0]
        except IndexError:
            return False
        self.b.execute_move(self.b[p1],p1,sel_move)
        self.switch_turn()
        return True
    def lose(self):
        self.done=True
        #self.comps[not self.turn].lastscore+=1

