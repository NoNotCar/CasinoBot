from . import Vector
from collections import defaultdict
from . import Pieces
P=Pieces.Piece
V=Vector.Vector2
class Board(object):
    theme=[(204,185,102),(124,69,32)]
    sidecols=[(255,0,0),(0,255,0)]
    lastmoved=None
    def __init__(self,size,cs):
        self.size=size
        self.board={}
        for x in range(self.size.x):
            self.spawn_fair(x,1,"Pawn")
        self.spawn_fair(0,0,cs[0])
        self.spawn_fair(7, 0, cs[0])
        self.spawn_fair(1, 0, cs[1])
        self.spawn_fair(6, 0, cs[1])
        self.spawn_fair(2, 0, cs[2])
        self.spawn_fair(5, 0, cs[2])
        self.spawn_fair(3, 0, cs[3])
        self.spawn_fair(4,0,"King")
        self.lost=[False,False]
    def __getitem__(self, item):
        return None if item not in self.board else self.board[item]
    def __setitem__(self, key, value):
        self.board[key]=value
    def spawn_fair(self,x,y,name):
        self[V(x,y)]=P(name,0)
        self[V(x,self.size.y-1-y)]=P(name,1)
    def in_board(self,pos):
        return pos.within(self.size)
    def valid(self,pos,side):
        tar=self[pos]
        return self.in_board(pos) and (tar is None or tar.side!=side and not tar.iron)
    def clear(self,pos):
        return self.in_board(pos) and self[pos] is None
    def iter_pieces(self,side):
        for pos,piece in list(self.board.items()):
            if piece and piece.side==side:
                yield piece,pos
    def get_moves(self, piece, pos):
        moves=set()
        for a in piece.atoms:
            moves.update(a.get_moves(piece, pos,pos,self))
        return moves
    def execute_move(self,piece,pos,m):
        last_royals=self.royals
        self.lastmoved=piece
        m.a.execute_move(piece,pos,m.v,self)
        for pos,piece in self.board.items():
            if piece and piece.promotes and (not pos.y if piece.side else pos.y==self.size.y-1):
                self[pos]=P(piece.promotes,piece.side)
        for s,r in enumerate(self.royals):
            if r<last_royals[s]:
                self.lost[s]=True
    @property
    def royals(self):
        return [len([p for p,pos in self.iter_pieces(s) if p.royal]) for s in range(2)]


