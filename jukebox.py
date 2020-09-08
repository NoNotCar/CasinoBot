from discord.ext import commands
from youtube_search import YoutubeSearch
import asyncio
import discord
import uuid
import pickle
import economy
import pathlib

DEFAULT_VOLUME = 0.15
MAX_LENGTH=600
MAX_AGE=100
def parse_duration(time:str):
    split=time.split(":")
    return sum(int(s)*(60**(len(split)-n-1)) for n,s in enumerate(split))
async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
        return True
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')
        return False
class CachedMusic(object):
    age=0
    def __init__(self,yt_link,id):
        self.link=yt_link
        self.id=id
        cache[yt_link]=self
    def delete(self):
        self.path.unlink()
        cache.pop(self.link)
    @property
    def path(self):
        return pathlib.Path('music_cache/%s.mp3' % self.id)
class QueuedMusic(object):
    def __init__(self,link,queuer:economy.User,desc:str):
        self.cm=cache[link] if link in cache else CachedMusic(link,str(uuid.uuid4()))
        self.queuer=queuer
        self.name=desc
    async def load(self):
        if self.cm.path.exists():
            return True
        if await run("youtube-dl -x --audio-format mp3 -o music_cache/" + self.cm.id + ".%(ext)s " + self.cm.link):
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


cache={}

class Jukebox(commands.Cog):
    vc=None
    queue_task=None
    happy=False
    def __init__(self, bot):
        self.bot = bot
        self.queue=[]
        for p in pathlib.Path("music_cache").glob("*.mp3"):
            p.unlink()
    @commands.command(name="search",help="search for youtube videos")
    async def search(self,ctx,*,query):
        result=YoutubeSearch(query,3).to_dict()
        print(result[0])
        await ctx.send("RESULTS: "+", ".join("https://www.youtube.com"+r["url_suffix"] for r in result))
    def search_for_one(self,query):
        result = YoutubeSearch(query).to_dict()
        for r in result:
            if parse_duration(r["duration"])<=MAX_LENGTH:
                return "https://www.youtube.com"+r["url_suffix"], "%s (%s)" % (r["title"],r["duration"])
        return None, None
    async def queue_music(self,ctx:commands.Context, qm:QueuedMusic, vc:discord.VoiceChannel):
        if not self.queue_task:
            self.queue_task=asyncio.create_task(self.manage_queue())
        if await qm.load():
            self.queue.append(qm)
        else:
            await ctx.send("Loading failed, your credits have been refunded")
            qm.queuer.update_balance(1)
            return
        if not self.vc:
            self.vc = await vc.connect()
    @commands.command(name="play",help="play the first result, costs 1c")
    async def play(self,ctx,*,query):
        euser = economy.get_user(ctx.author)
        if not (self.happy or euser.credits):
            await ctx.send("Sorry, you're broke!")
            return
        result, desc = self.search_for_one(query)
        if not result:
            await ctx.send("Sorry, couldn't find any results for %s" % query)
            return
        user = ctx.message.author
        if user.voice:
            if not self.happy:
                euser.update_balance(-1)
            vc=user.voice.channel
            await ctx.send("**%s** added to queue!" % desc)
            if not self.queue and result not in cache:
                await ctx.send("Loading music...")
            await self.queue_music(ctx,QueuedMusic(result,euser,desc),vc)
        else:
            await ctx.send("How are you meant to listen to music if you're not in a voice channel?")
    @commands.command(name="queue",help="View the current music queue")
    async def view_queue(self,ctx):
        if self.queue:
            await ctx.send("\n".join("#%s: %s" % (n+1,qm.name) for n,qm in enumerate(self.queue[:10])))
        else:
            await ctx.send("There's no music queued - did you mean $play?")
    async def manage_queue(self):
        try:
            while True:
                if self.queue and self.vc:
                    await self.queue[0].load()
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
    @commands.is_owner()
    @commands.command(name="jukenot",help="stop all music and clear the queue")
    async def stop(self,ctx):
        if self.vc:
            self.vc.stop()
            self.queue=[]
        else:
            await ctx.send("No music to stop!")
    @commands.command(name="skip",help="skip the current song, costs 5c if you didn't queue it")
    async def skip(self,ctx,idx:int=1):
        payer=economy.get_user(ctx.author)
        if idx<1 or len(self.queue)<idx:
            await ctx.send("Index out of range" if idx else "No music to skip!")
            return
        song=self.queue[idx-1]
        own=song.queuer==payer
        cost=0 if own or self.happy else 5
        if payer.update_balance(-cost):
            if not own and not self.happy:
                await ctx.send("%s has been refunded 1c" % song.queuer.name)
                song.queuer.update_balance(1)
            if idx==1:
                self.vc.stop()
            else:
                self.queue.remove(song)
        else:
            await ctx.send("You don't have enough money to skip this!")
    @commands.is_owner()
    @commands.command(name="happyhour",help="disable jukebox costs for this runtime")
    async def happy_hour(self,ctx):
        self.happy=True
        await ctx.send("IT'S HAPPY HOUR! ALL JUKEBOX FUNCTIONS ARE FREE!")
    async def graceful_stop(self):
        if self.queue_task:
            self.queue_task.cancel()
            await self.queue_task
    def cog_unload(self):
        print("AIEEEEE")