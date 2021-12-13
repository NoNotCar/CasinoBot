from __future__ import annotations

import pathlib
import typing
from PIL import Image, ImageFont, ImageDraw
import vector
from asyncio import Lock
import discord
from dib import BasePlayer

bebas = ImageFont.truetype("fonts/bebas.ttf",16)
templock = Lock()
class PImg(object):
    def __init__(self, img:Image.Image):
        self.img=img
    def xn(self,n)->PImg:
        return PImg(self.img.resize((self.w*n,self.h*n),Image.NEAREST))
    def blit(self,other:PImg,pos:vector.V2):
        self.img.paste(other.img, (pos.x, pos.y, pos.x + other.w, pos.y + other.h), other.img)
    def write(self,text:str,font:ImageFont.ImageFont,pos:vector.V2,anchor="mm",colour=(0,0,0)):
        d=ImageDraw.Draw(self.img)
        d.text(pos,text,font=font,anchor=anchor,fill=colour)
    def copy(self):
        return PImg(self.img.copy())
    def save(self,filename):
        self.img.save(filename)
    async def send(self,channel:discord.TextChannel):
        async with templock:
            self.save("temp.png")
            await channel.send(file=discord.File("temp.png"))
    async def dm_send(self,player:BasePlayer,msg=""):
        async with templock:
            self.save("temp.png")
            await player.dm(msg,file=discord.File("temp.png"))
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
