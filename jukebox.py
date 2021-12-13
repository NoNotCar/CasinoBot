from discord.ext import commands
from youtube_search import YoutubeSearch
import asyncio
import discord
import uuid
import pickle
import pathlib
import os
import requests
from bottoken import api
from difflib import SequenceMatcher
from random import choice, shuffle
from collections import defaultdict
DEFAULT_VOLUME = 0.15
MAX_LENGTH=12*60
MAX_AGE=100
cache_loc="E:\music_cache"
def parse_duration(time:str):
    split=time.split(":")
    return sum(int(s)*(60**(len(split)-n-1)) for n,s in enumerate(split))
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()
def parse_duration_2(time:str):
    print(time)
    time=time[2:]
    if "H" in time:
        return 3600
    if "M" in time:
        split=time.split("M")
        split[1]=split[1][:-1]
        return sum((int(s) if s else 0) * (60 ** (len(split) - n - 1)) for n, s in enumerate(split))
    elif "S" in time:
        return int(time[:-1])
    return 9999
def pickleload(file,default=None):
    try:
        with open(file,"rb") as f:
            return pickle.load(f)
    except IOError:
        return default
async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode==1:
        return False
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
        return stdout.decode()
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')
        return False
class FileDict(object):
    def __init__(self,file):
        self.obj=pickleload(file,{})
        self.file=file
    def __getattr__(self, item):
        if item in ["obj","file"]:
            return self.__dict__[item]
        else:
            return getattr(self.obj,item)
    def __getitem__(self, item):
        return self.obj[item]
    def __setitem__(self, key, value):
        self.obj[key]=value
        self.sync()
    def __contains__(self, item):
        return item in self.obj
    def sync(self):
        sobj=pickleload(self.file,{})
        for k,v in self.obj.items():
            sobj[k]=v
        self.obj=sobj
        with open(self.file,"wb") as f:
            pickle.dump(sobj,f)
class CachedMusic(object):
    age=0
    def __init__(self,yt_link,id):
        self.link=yt_link
        self.id=id
        cache[yt_link]=self
    @property
    def path(self):
        return pathlib.Path(cache_loc+"/%s.mp3" % self.id)
class QueuedMusic(object):
    def __init__(self,link,desc:str,queuer:discord.User):
        self.cm=cache[link] if link in cache else CachedMusic(link,str(uuid.uuid4()))
        self.name=desc
        self.queuer=queuer
    async def load(self):
        if self.loaded:
            return True
        if await run("youtube-dl -x --audio-format mp3 -o "+cache_loc+"\\" + self.cm.id + ".%(ext)s " + self.cm.link):
            return True
        else:
            return False
    async def play(self,vc):
        self.cm.age=0
        audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.cm.path),
                                                    DEFAULT_VOLUME)
        vc.play(audio_source)
        while vc.is_playing():
            await asyncio.sleep(1)
    @property
    def loaded(self):
        return self.cm.path.exists()


cache=FileDict("music.cache")
search_cache=FileDict("search.pickle")
alias_cache=FileDict("alias.pickle")
class Jukebox(commands.Cog):
    vc=None
    queue_task=None
    happy=False
    DODGY=False
    current_track = None
    def __init__(self, bot):
        self.bot = bot
        self.queue=[]
        self.skip_banned=set()
    def offical_search(self,query, results=10, max_duration=600):
        response = requests.get(
            "https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=%s&q=%s&type=video&key=%s" % (
            results, query, api), timeout=1.0)
        if response.ok:
            json = response.json()
            if "items" in json:
                ids=[i["id"]["videoId"] for i in json["items"]]
                ids=",".join(ids)
                durationresponse=requests.get(f"https://www.googleapis.com/youtube/v3/videos?id={ids}&part=contentDetails&key={api}")
                if durationresponse.ok:
                    djson=durationresponse.json()
                    if "items" in djson:
                        for n,i in enumerate(djson["items"]):
                            duration=parse_duration_2(i["contentDetails"]["duration"])
                            if duration<=max_duration:
                                return "https://www.youtube.com/watch?v="+i["id"], "%s (%s)" % (json["items"][n]["snippet"]["title"],"%s:%02d"%(duration//60,duration%60))
        return None, None
    @commands.command(name="search",help="search for youtube videos")
    async def search(self,ctx,*,query):
        result=YoutubeSearch(query,3).to_dict()
        print(result[0])
        await ctx.send("RESULTS: "+", ".join("https://www.youtube.com"+r["url_suffix"] for r in result))
    async def search_for_one(self,query,ctx):
        query=query.lower()
        if query in search_cache:
            return search_cache[query]
        await ctx.send("Search not in cache, trying official search...")
        url,info=self.offical_search(query,max_duration=MAX_LENGTH)
        if url:
            search_cache[query]=url,info
            return url,info
        else:
            if self.DODGY:
                await ctx.send("Official search failed, trying dodgy search...")
                result = YoutubeSearch(query,3).to_dict()
                for r in result:
                    if r["duration"] and parse_duration(r["duration"])<=MAX_LENGTH:
                        search_cache[query]="https://www.youtube.com"+r["url_suffix"], "%s (%s)" % (r["title"],r["duration"])
                        return search_cache[query]
                search_cache[query]=None,None
            else:
                await ctx.send("Official search failed, giving up...")
        return None, None
    async def queue_music(self,ctx:commands.Context, qm:QueuedMusic, vc:discord.VoiceChannel,load=True):
        if not self.queue_task:
            self.queue_task=asyncio.create_task(self.manage_queue())
        if not load or await qm.load():
            self.queue.append(qm)
            self.resort()
        else:
            await ctx.send("Loading failed, sorry!")
            return
        if not self.vc:
            self.vc = await vc.connect()
        return qm
    @commands.command(name="cache",help="view what's in cache, with optional search feature")
    async def cache(self,ctx,*,query=""):
        results=sorted(search_cache.keys(),key=lambda s:similar(query,s) if query else s,reverse=bool(query))[:10 if query else 50]
        await ctx.send(", ".join(results))
    @commands.command(name="play",help="play the first result")
    async def play(self,ctx,*,query):
        result, desc = await self.search_for_one(query,ctx)
        if not result:
            await ctx.send("Sorry, couldn't find any results for %s" % query)
            return
        user = ctx.message.author
        if user.voice:
            vc=user.voice.channel
            await ctx.send("**%s** added to queue!" % desc)
            if not self.queue and result not in cache:
                await ctx.send("Loading music...")
            return await self.queue_music(ctx,QueuedMusic(result,desc,user),vc)
        else:
            await ctx.send("How are you meant to listen to music if you're not in a voice channel?")
    @commands.command(name="insert",help="play music ahead of your other queued tracks")
    async def insert(self,ctx,*,query):
        qm = await self.play(ctx,query=query)
        if qm and len(self.queue)>1:
            self.queue.remove(qm)
            self.queue.insert(1,qm)
            self.resort()
    @commands.command(name="sudoplay",help="play a direct youtube link, bypassing search.")
    @commands.is_owner()
    async def sudoplay(self,ctx,url):
        user = ctx.message.author
        qm=QueuedMusic(url, "Unknown (N/A)",user)
        if user.voice:
            vc = user.voice.channel
            await ctx.send("**%s** added to queue!" % qm.name)
            if not self.queue and url not in cache:
                await ctx.send("Loading music...")
            await self.queue_music(ctx,qm, vc)
        else:
            await ctx.send("How are you meant to listen to music if you're not in a voice channel?")
    @commands.command(name="queue",help="View the current music queue")
    async def view_queue(self,ctx,page=1):
        start = 10*(page-1)
        if start<len(self.queue):
            await ctx.send("\n".join("#%s: %s" % (start+n+1,qm.name) for n,qm in enumerate(self.queue[start:start+10])))
        else:
            await ctx.send("There's no music on that queue page - did you mean $play?")
    @commands.command(name="playlist",help="Queue an entire playlist")
    async def queue_playlist(self,ctx,url,shuff=""):
        url=self.aliased(url)
        user = ctx.message.author
        if user.voice:
            vc = user.voice.channel
        else:
            await ctx.send("STOP TRYING TO LISTEN TO MUSIC WITHOUT BEING IN THE CHANNEL")
            return
        result = await run("youtube-dl --flat-playlist --get-id --get-title --get-duration %s" % url)
        if result:
            result = result.split("\n")
            skipped = 0
            added = 0
            qms=[]
            for i,title in enumerate(result[::3]):
                if title:
                    vid = "https://www.youtube.com/watch?v=%s" % result[i*3+1]
                    d = parse_duration(result[i*3+2])
                    if d<=MAX_LENGTH:
                        qms.append(QueuedMusic(vid,"%s (%s)" % (title,result[i*3+2]),user))
                        added+=1
                    else:
                        skipped+=1
            if shuff.lower() in ["shuffle","shuffled"]:
                shuffle(qms)
            for q in qms:
                await self.queue_music(ctx,q, vc, False)
            await ctx.send("%s tracks added to queue, %s skipped due to length" % (added,skipped))
        else:
            await ctx.send("Sorry, that link didn't work...")
    async def manage_queue(self):
        try:
            while True:
                if self.queue and self.vc:
                    await self.queue[0].load()
                    if len(self.queue)>1:
                        asyncio.create_task(self.queue[1].load())
                    await self.queue[0].play(self.vc)
                    self.queue.pop(0)
                elif self.vc:
                    await self.vc.disconnect()
                    self.vc=None
                else:
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            if self.vc:
                self.vc.stop()
                await self.vc.disconnect()
        except Exception as e:
            print("Ignoring exception %s, and resetting..." % e)
            self.queue_task=asyncio.create_task(self.manage_queue())
    @commands.is_owner()
    @commands.command(name="jukenot",help="stop all music and clear the queue")
    async def stop(self,ctx):
        if self.vc:
            self.queue=[]
            self.mood_music=None
            self.vc.stop()
        else:
            await ctx.send("No music to stop!")
    @commands.is_owner()
    @commands.command(name="skipban",help="stop CERTAIN PEOPLE from skipping other people's music")
    async def skipban(self,ctx,user:discord.Member):
        if user in self.skip_banned:
            await ctx.send(f"{user.nick} has been un-skipbanned.")
            self.skip_banned.remove(user)
        else:
            await ctx.send(f"{user.nick} has been skipbanned!")
            self.skip_banned.add(user)
    @commands.command(name="skip",help="skip the current song")
    async def skip(self,ctx,idx:int=1):
        target = self.queue[idx-1]
        if target.queuer!=ctx.author and ctx.author in self.skip_banned:
            await ctx.send("Sorry, you've been skipbanned. Take a moment to reflect on your wrongdoings...")
            return
        if idx==1 and self.vc:
            self.vc.stop()
            return
        if idx<1 or len(self.queue)<idx:
            await ctx.send("Index out of range" if idx else "No music to skip!")
            return
        song=self.queue[idx-1]
        self.queue.remove(song)
        self.resort()
        await ctx.send("%s removed from queue!" % song.name)
    @commands.command(name="clear",help="clear all your music (except for the currently playing one)")
    async def clear(self,ctx):
        cleared=0
        for qm in self.queue[1:]:
            if qm.queuer == ctx.author:
                self.queue.remove(qm)
                cleared+=1
        await ctx.send("Cleared %s queue entries!" % cleared)
    @commands.command(name="shuffle",help="shuffle your queued music")
    async def shuffle(self,ctx):
        to_shuffle = []
        for qm in self.queue[1:]:
            if qm.queuer==ctx.author:
                to_shuffle.append(qm)
                self.queue.remove(qm)
        shuffle(to_shuffle)
        self.queue.extend(to_shuffle)
        self.resort()
        await ctx.send("Shuffled %s queue entries!" % len(to_shuffle))
    def aliased(self,thing):
        if thing in alias_cache:
            return alias_cache[thing]
        return thing
    @commands.command(name="alias",help="create an alias for faster queueing")
    async def alias(self,ctx,alias:str,url:str):
        if "/" in alias:
            await ctx.send("Warning - alias contains /, check you got the arguments the right way round...")
        if ctx.author==ctx.guild.owner or alias not in alias_cache:
            alias_cache[alias]=url
        await ctx.send("Alias creation successful!")
    def resort(self):
        if self.queue and len(self.queue)>1:
            counters = {}
            cdict = {}
            for qm in self.queue:
                if qm.queuer not in counters:
                    counters[qm.queuer]=0.01*len(counters)
                counters[qm.queuer]+=1
                cdict[qm]=counters[qm.queuer]
            self.queue.sort(key=lambda qm:cdict[qm])
    async def graceful_stop(self):
        if self.queue_task:
            self.queue_task.cancel()
            await self.queue_task
    def cog_unload(self):
        print("AIEEEEE")