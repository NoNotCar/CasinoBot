from backend import Vector
import math
import re
from . import Pieces
import random
import copy
from functools import reduce
right=math.pi/2
pi=math.pi
V=Vector.Vector2
class Movement(object):
    origin=None
    def __init__(self,move,atom):
        self.v=move
        self.a=atom
    def __eq__(self, other):
        return self.v==other.v
    def __hash__(self):
        return hash(self.v)
class Atom(object):
    mcol=(192,192,192)
    seltype=0
    limit=None
    def get_moves(self, piece, pos, origin, board):
        return set()
    def execute_move(self,piece,pos,v,board):
        tar=board[pos+v]
        board[pos]=None
        board[pos+v]=None if tar and tar.deathtouch else piece
    def limited(self, limit):
        new = copy.deepcopy(self)
        new.limit = limit
        return new
class Jumper(Atom):
    def __init__(self,v):
        self.vectors=frozenset(v.rots()+V(-v.x,v.y).rots())
    def get_moves(self, piece, pos, origin, board):
        return set(Movement(v,self) for v in self.vectors if board.valid(v+pos,piece.side))
class Slider(Jumper):
    def get_moves(self, piece, pos, origin, board):
        moves=set()
        for v in self.vectors:
            p=Vector.zero
            n=1
            while board.clear(pos+p+v) and (not self.limit or n<self.limit):
                n+=1
                p+=v
                moves.add(p)
            if board.valid(pos+p+v,piece.side):
                moves.add(p+v)
        return set(Movement(v,self) for v in moves)
class Teleport(Atom):
    mcol = (100, 100, 200)
    def get_moves(self, piece, pos, origin, board):
        moves=set()
        for p in board.size.iter_locs():
            if board.clear(p):
                moves.add(Movement(p-pos,self))
        return moves
class SwitchWitch(Atom):
    mcol=(255,216,100)
    def get_moves(self, piece, pos, origin, board):
        return set(Movement(p-pos,self) for pic,p in board.iter_pieces(piece.side) if p!=pos)
    def execute_move(self,piece,pos,v,board):
        board[pos]=board[pos+v]
        board[pos+v]=piece
class Mime(Atom):
    def get_moves(self, piece, pos, origin, board):
        if board.lastmoved:
            nonmime=[a.get_moves(piece, pos, origin, board) for a in board.lastmoved.atoms if not isinstance(a, Mime)]
            if nonmime:
                return reduce(lambda a,b:a|b,nonmime)
        return set()
class Modifier(Atom):
    def __init__(self,atom):
        self.atom=atom
    def is_valid(self, v, piece, pos, origin, board):
        return True
    def get_moves(self, piece, pos, origin, board):
        return set(Movement(m.v,self) for m in self.atom.get_moves(piece, pos, origin,board) if
                   self.is_valid(m.v, piece, pos, origin, board))
class CrookedSlider(Modifier):
    def get_moves(self, piece, pos, origin, board):
        moves=set()
        for v in self.atom.vectors:
            for d in [3,1]:
                p=Vector.zero
                n=1
                av=v
                while board.clear(pos+p+av) and (not self.limit or n<self.limit):
                    n+=1
                    p+=av
                    av=(v if n%2 else v.rotated(d))
                    moves.add(p)
                if board.valid(pos+p+av,piece.side):
                    moves.add(p+av)
        return set(Movement(v,self) for v in moves)
class Forward(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        if piece.side:
            return v.y<0
        return v.y>0
class Backward(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        if piece.side:
            return v.y>0
        return v.y<0
class Sideways(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        return v.x
class Wide(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        return abs(v.x)>abs(v.y)
class Narrow(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        return abs(v.x)<abs(v.y)
class Attacking(Modifier):
    mcol=(200,100,100)
    def is_valid(self, v, piece, pos, origin, board):
        return board[v+pos] is not None
class Moving(Modifier):
    mcol=(100,100,200)
    def is_valid(self, v, piece, pos, origin, board):
        return board[v+pos] is None
class Withdrawer(Moving):
    mcol = (200,100,200)
    def execute_move(self,piece,pos,v,board):
        board[pos]=None
        board[pos+v]=piece
        dpos=pos-v//v.smil
        if board[dpos] and board[dpos].side!=piece.side and not board[dpos].iron:
            board[dpos]=None
class Rammer(Moving):
    mcol = (255,155,0)
    def execute_move(self,piece,pos,v,board):
        board[pos] = None
        board[pos + v] = piece
        dpos=pos+v+v//v.smil
        if board[dpos] and board[dpos].side!=piece.side and not board[dpos].iron:
            board[dpos]=None
class First(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        if piece.side:
            return pos.y>=board.size.y-2
        return pos.y<=1
class Lame(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        uv=v//v.smil
        for n in range(1,v.smil):
            if not board.clear(pos+uv*n):
                return False
        return True
class Jumping(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        uv=v//v.smil
        for n in range(1,v.smil):
            if board.clear(pos+uv*n):
                return False
        return True
class Edge(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        uv = v // v.smil
        for n in range(1, v.smil):
            tpos=pos + uv * n
            if tpos.x not in [0,board.size.x-1] and tpos.y not in [0,board.size.y-1]:
                return False
        return True
class Spacious(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        uv = v // v.smil
        return board.clear(pos+v+uv)
class Outwards(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        return v.anglediff(origin-pos)>right-0.01
class MoreOut(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        return v.anglediff(origin-pos)>3*right/2+0.01
class Inwards(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        return v.anglediff(origin-pos)<right-0.01
class Left(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        return -pi+0.01<v.angle(origin-pos)<-0.01
class Right(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        return 0.01<v.angle(origin-pos)<pi-0.01
class Straight(Modifier):
    def is_valid(self, v, piece, pos, origin, board):
        return v.anglediff(origin-pos)>pi-0.01
class Viral(Modifier):
    mcol = (155,255,0)
    def execute_move(self,piece,pos,v,board):
        if board[pos+v] and not any(isinstance(a,Viral) for a in board[pos+v].atoms):
            board[pos+v]=Pieces.Piece(piece.name,piece.side)
        else:
            Atom.execute_move(self,piece,pos,v,board)
class Projectile(Modifier):
    mcol = (255,155,0)
    seltype = 1
    def is_valid(self, v, piece, pos, origin, board):
        return board[v + pos] is not None
    def execute_move(self,piece,pos,v,board):
        board[pos+v]=None
class Dice(Modifier):
    mcol=(255,0,255)
    def execute_move(self,piece,pos,v,board):
        attack=board[pos+v]
        Modifier.execute_move(self,piece,pos,v,board)
        if attack:
            board[pos+v]=Pieces.Piece(random.choice(Pieces.titans),piece.side)
class Combo(Atom):
    def __init__(self,a1,a2):
        self.firsts=a1
        self.seconds=a2
    def get_moves(self, piece, pos, origin, board):
        moves=set()
        for f in self.firsts:
            for m in f.get_moves(piece, pos, origin,board):
                moves.add(m)
                if board.clear(m.v+pos):
                    for s in self.seconds:
                        moves.update(Movement(m.v+om.v,s) for om in s.get_moves(piece, pos + m.v,origin,board))
        return moves
atoms={"W":Jumper(V(1,0)),
       "F":Jumper(V(1,1)),
       "D":Jumper(V(2,0)),
       "N": Jumper(V(2, 1)),
       "A": Jumper(V(2, 2)),
       "H": Jumper(V(3, 0)),
       "R": Slider(V(1, 0)),
       "B": Slider(V(1, 1)),
       "T":Teleport(),
       "M": Mime(),
       "S":SwitchWitch()}
mods={"f":Forward,
      "b":Backward,
      "s":Sideways,
      "w":Wide,
      "n":Narrow,
      "a":Attacking,
      "m":Moving,
      "p":First,
      "l":Lame,
      "j":Jumping,
      "o":Outwards,
      "/":MoreOut,
      "i":Inwards,
      "<":Left,
      ">":Right,
      "|":Straight,
      "v":Viral,
      "!":Projectile,
      "?":Withdrawer,
      "r":Rammer,
      "%":Dice,
      "e":Edge,
      "$":Spacious,
      "z":CrookedSlider}
def parse(string):
    esplit=re.split("[\[\]]",string)
    if len(esplit)>1:
        return parse(esplit[0])[0],esplit[1]
    csplit=string.split(",")
    if len(csplit)>1:
        return sum((parse(s)[0] for s in csplit),[]),""
    split=string.split("-",1)
    if len(split)==2:
        return [Combo(*[parse(s)[0] for s in split])],""
    ats=[]
    lastatom=None
    limit=None
    for char in reversed(string):
        if char in "123456789":
            limit=int(char)
        elif char in atoms:
            if lastatom:
                ats.append(lastatom)
            lastatom=atoms[char].limited(limit) if limit else atoms[char]
            limit=0
        else:
            lastatom=mods[char](lastatom)
    return ats+[lastatom],""