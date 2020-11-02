from __future__ import annotations

import pathlib
import typing
from PIL import Image, ImageFont, ImageDraw
import vector

class PImg(object):
    def __init__(self, img:Image.Image):
        self.img=img
    def xn(self,n)->PImg:
        return PImg(self.img.resize((self.w*n,self.h*n),Image.NEAREST))
    def blit(self,other:PImg,pos:vector.V2):
        self.img.paste(other.img, (pos.x, pos.y, pos.x + other.w, pos.y + other.h), other.img)
    def copy(self):
        return PImg(self.img.copy())
    @classmethod
    def filled(cls,sz:vector.V2,color:tuple)->PImg:
        return PImg(Image.new("RGBA",sz.tuple,color))
    @property
    def h(self):
        return self.img.height
    @property
    def w(self):
        return self.img.width

def load(path:typing.Union[str, pathlib.Path])->PImg:
    return PImg(Image.open(path).convert("RGBA"))

def strip(path,w=None):
    i = load(path)
    imgs = []
    if w is None:
        w=i.h
    for n in range(i.w// w):
        imgs.append(PImg(i.img.crop((n*w,0,n*w+w,i.h))))
    return imgs
