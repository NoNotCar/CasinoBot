from . import PImg
from .Atoms import parse
class Piece(object):
    royal=False
    promotes=False
    flips=False
    deathtouch=False
    iron=False
    def __init__(self,name,side):
        self.name=name
        self.side=side
        self.atoms,extra=parse(pnots[name])
        for e in extra.split(","):
            if e:
                if "=" in e:
                    self.__setattr__(*e.split("="))
                else:
                    self.__setattr__(e,True)
class PieceImageManager(PImg.KeyedImageManager):
    def __init__(self,base):
        self.base= base, base.vflip()
        PImg.KeyedImageManager.__init__(self)
    def gen_img(self,args):
        return tuple(PImg.supercolcopy(b, args) for b in self.base)
pimgs={}
pnots={}
pexp={}
def p_load(fname):
    nps=[]
    with open(PImg.np(PImg.loc + "%s.pcs" % fname)) as f:
        for line in f.readlines():
            if line[-1]=="\n":
                line=line[:-1]
            name,notation,exp=line.split(":")
            nps.append(name)
            p_reg(name,notation,exp)
    return nps
def p_reg(name,notation,explain):
    pnots[name] = notation
    pimgs[name] = PieceImageManager(PImg.imgx("Pieces/" + name))
    pexp[name]=explain
titans=p_load("titans")
guards=p_load("guards")
shock=p_load("shock")
forts=p_load("forts")
p_reg("Pawn","mplfDmfWafF[promotes=Queen]","Your modal soldier, always promotes to queen")
p_reg("King","FW[royal]","Protect from capture")