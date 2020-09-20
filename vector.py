from __future__ import annotations
import math
import typing
class V2(object):
    __slots__ = "x","y"
    def __init__(self,x,y):
        self.x=x
        self.y=y
    def __add__(self, other)->V2:
        return V2(self.x + other.x, self.y + other.y)
    def __sub__(self, other)->V2:
        return V2(self.x - other.x, self.y - other.y)
    def __mul__(self, other)->V2:
        if isinstance(other, V2):
            return V2(self.x * other.x, self.y * other.y)
        else:
            return V2(self.x * other, self.y * other)
    def __truediv__(self, other)->V2:
        return self*(1/other)
    def __floordiv__(self, other)->V2:
        return V2(self.x // other, self.y // other)
    def __eq__(self, other):
        return (self.x,self.y)==(other.x,other.y)
    def __ne__(self, other):
        return not self==other
    def __hash__(self):
        return hash((self.x,self.y))
    def __len__(self):
        return 2
    def __repr__(self):
        return "V2(%s,%s)"%(self.x,self.y)
    def __neg__(self)->V2:
        return self*-1
    def __getitem__(self, item):
        assert isinstance(item,int)
        return self.y if item else self.x
    def __abs__(self)->V2:
        return V2(abs(self.x), abs(self.y))
    def __bool__(self):
        return self.x or self.y
    def within(self, other):
        return 0<=self.x<other.x and 0<=self.y<other.y
    def unit(self)->V2:
        try:
            return self/self.rlen
        except ZeroDivisionError:
            return zero
    def copy(self)->V2:
        return V2(self.x, self.y)
    def rotated(self,r)->V2:
        if not r:
            return self.copy()
        elif r==1:
            return V2(-self.y, self.x)
        elif r==2:
            return -self
        else:
            return V2(self.y, -self.x)
    def rots(self)->typing.List[V2]:
        return [self.rotated(r) for r in range(4)]
    def iter_locs(self):
        for x in range(self.x):
            for y in range(self.y):
                yield V2(x, y)
    def anglediff(self,other):
        return math.acos((self.x*other.x+self.y*other.y)/(self.rlen*other.rlen))#
    def angle(self,other):
        dot = self.x*other.x+self.y*other.y  # dot product between [x1, y1] and [x2, y2]
        det = self.x*other.y-self.y*other.x  # determinant
        return math.atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)
    @property
    def tuple(self):
        return self.x,self.y
    @property
    def rlen(self):
        return (self.x**2+self.y**2)**0.5
    @property
    def smil(self):
        return max(abs(self.x),abs(self.y))
    @property
    def int(self)->V2:
        return V2(int(self.x), int(self.y))

zero=V2(0,0)
one=V2(1,1)
left=V2(-1,0)
up=V2(0,-1)
right=V2(1,0)
down=V2(0,1)
around=[up,right,down,left]

def iter_offsets(tpos:V2):
    for a in around:
        yield tpos+a