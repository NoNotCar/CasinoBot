__author__ = 'NoNotCar'
from PIL import Image, ImageFont, ImageDraw
import os
from random import choice, randint
import math
import colorsys
from itertools import count
from collections import defaultdict
from .Vector import Vector2

tau = math.pi * 2
hpi = math.pi / 2

np = os.path.normpath
loc = os.getcwd() + "/backend/Assets/"
from . import Colour

class ScaledImage(object):
    def __init__(self,img:Image.Image):
        self.imgs=(img,)+tuple(xn(img,n) for n in (2,3,4,5))
        self.img=img
        self.h,self.w=img.size
    def copy(self):
        return ScaledImage(self.img.copy())
    def vflip(self):
        return ScaledImage(self.img.transpose(Image.FLIP_TOP_BOTTOM))
    def __getitem__(self, item):
        return self.imgs[item]
def img(fil:str)->Image.Image:
    return Image.open(np(loc + fil + ".png")).convert("RGBA")
def imgx(fil):
    i=img(fil)
    return ScaledImage(i)
def imgn(fil,n):
    return xn(img(fil),n)
def xn(i:Image.Image,n:int)->Image.Image:
    return i.resize((i.width*n,i.height*n),Image.NEAREST)
def ftrans(f,folder):
    return lambda x: f(folder+"/"+x)

def imgstripx(fil,w=None):
    i = img(fil)
    imgs = []
    h=i.height
    if w is None:
        w=h
    for n in range(i.width// w):
        imgs.append(ScaledImage(i.crop((n*w,0,n*w+w,h))))
    return imgs
def tilemapx(fil,sz=16):
    if isinstance(fil,str):
        i = img(fil)
    else:
        i=fil
    imgs = []
    h=i.height
    w=i.width
    for y in range(h // sz):
        for x in range(w // sz):
            imgs.append(ScaledImage(i.crop((x*sz,y*sz,x*sz+sz,y*sz+sz))))
    return imgs
"""class UltraTiles(object):
    blank=imgx("Blank")
    def __init__(self,fil,*ccs):
        tiles=imgstripx(fil)
        for n,cc in enumerate(ccs):
            if n:
                [colswap(t, cc[0], cc[1]) for t in tiles]
            else:
                [colswap(t, (128,)*3, cc) for t in tiles]
        self.tiles=[tilesplit(t) for t in tiles]
        self.cache={}
    def __getitem__(self, item):
        try:
            return self.cache[item]
        except KeyError:
            tile=self.blank.copy()
            for n,t in enumerate(item):
                tile.blit(self.tiles[t][n],(n%2*8,n//2*8))
            self.cache[item]=tile
            return tile"""
def imgstripxfs(fil,ws):
    i = img(fil)
    imgs = []
    h = i.height
    cw=0
    for w in ws:
        imgs.append(ScaledImage(i.crop((cw,0,cw+w,h))))
        cw+=w
    return imgs
def imgrot(i:ScaledImage,r=4):
    imgs=[i]
    for n in range(1,r):
        imgs.append(ScaledImage(imgs[-1].img.copy().transpose(Image.ROTATE_90)))
    return imgs
def imgstriprot(fil,r=4):
    return [imgrot(i,r) for i in imgstripx(fil)]
def irot(i:Image.Image,n):
    return ScaledImage(i.transpose([Image.ROTATE_90,Image.ROTATE_180,Image.ROTATE_270][n]))

def bcentre(font:ImageFont.ImageFont, text, surface:Image.Image, offset=0, col=(0, 0, 0), xoffset=0):
    draw=ImageDraw.Draw(surface)
    tsize = draw.textsize(text,font)
    draw.text((surface.width/2-tsize[0]/2+xoffset,surface.height/2-tsize[1]/2+offset),text,col,font)

def bcentrex(font:ImageFont.ImageFont, text, surface:Image.Image, y, col=(0, 0, 0), xoffset=0):
    draw = ImageDraw.Draw(surface)
    tsize = draw.textsize(text, font)
    draw.text((surface.width / 2 - tsize[0] / 2 + xoffset, y), text, col, font)
# def cxblit(source, dest, y, xoff=0):
#     srect=source.get_rect()
#     drect=dest.get_rect()
#     srect.centerx=drect.centerx+xoff
#     srect.top=y
#     return dest.blit(source,srect)

def colswap(img,sc,ec):
    if isinstance(img,Image.Image):
        pix=img.load()
        for x in range(img.width):
            for y in range(img.height):
                if pix[x,y][3]==255 and pix[x,y][:3]==sc:
                    img.putpixel((x,y),ec)

    else:
        for i in img.imgs:
            colswap(i,sc,ec)
    return img
def colcopy(i,sc,ec):
    i=i.imgs[0].copy()
    colswap(i,sc,ec)
    return ScaledImage(i)
def multicolcopy(img,*args):
    img=colcopy(img,*args[0])
    for s,e in args[1:]:
        colswap(img,s,e)
    return img
def supercolcopy(img,col):
    return multicolcopy(img,((255,255,255),col),((192,192,192),Colour.darker(col,0.75)),((191,191,191),Colour.darker(col,0.75)),((128,128,128),Colour.darker(col)),((64,64,64),Colour.darker(col,0.25)))
imss=[]
class ImageManager(object):
    def __init__(self):
        self.imgs={}
        imss.append(self)
    def register(self):
        used=list(self.imgs.keys())
        new= next((n for n in count() if n not in used))
        self[new]
        return new
    def gen_img(self):
        return None
    def __getitem__(self, item):
        try:
            return self.imgs[item]
        except KeyError:
            ni=self.gen_img()
            self.imgs[item]=ni
            return ni
    def reload(self):
        self.imgs={}
class RandomImageManager(ImageManager):
    def __init__(self,imgs,cf,sc=(128,128,128)):
        self.i=imgs
        self.cf=cf
        self.sc=sc
        ImageManager.__init__(self)
    def gen_img(self):
        return colcopy(choice(self.i),self.sc,self.cf())
class KeyedImageManager(object):
    def __init__(self):
        self.imgs={}
    def gen_img(self,args):
        return None
    def __getitem__(self, args):
        try:
            return self.imgs[args]
        except KeyError:
            ni=self.gen_img(args)
            self.imgs[args]=ni
            return ni
class SuperImageManager(KeyedImageManager):
    def __init__(self,base):
        self.base=base
        KeyedImageManager.__init__(self)
    def gen_img(self,args):
        return supercolcopy(self.base,args)
class ColourGenerator(object):
    def __init__(self,min_sat,cd=None):
        self.ms=min_sat
        self.cd=cd
        self.gen_cols=set()
    def __call__(self, *args, **kwargs):
        while True:
            nc=tuple(randint(0,255) for _ in range(3))
            if max(nc)-min(nc)>=self.ms:
                if self.cd is None:
                    return nc
                for c in self.gen_cols:
                    cd=sum(abs(c[n]-nc[n]) for n in range(3))
                    if cd<=self.cd:
                        break
                else:
                    self.cd+=1
                    self.gen_cols.add(nc)
                    return nc
                self.cd-=1
def fload(fil,sz=16):
    return ImageFont.truetype(np(loc+fil+".ttf"),sz)

def blit(src:Image.Image,dest:Image.Image,pos:Vector2):
    dest.paste(src,(pos.x,pos.y,pos.x+src.width,pos.y+src.height),src)
# prog=imgx("Progress")
# def draw_progress(world,pos,p,col=(0,255,0)):
#     world.blit(prog,pos,oy=-4)
#     pygame.draw.rect(world.screen,col,pygame.Rect(world.screen_space(pos,ox=1,oy=-3),(world.cam_scale*p*14//16,world.cam_scale//8)))