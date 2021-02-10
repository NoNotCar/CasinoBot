from __future__ import annotations
import discord
from discord.ext import commands
from economy import get_user, register_1v1, register_ranked
import asyncio
import random
import typing
import string
from collections import defaultdict
dib_games=[]
fake_names=["Amelia","Bob","Callum","Derek","Emily","Fergus","Gordon","Harry","Isobel","John","Kallum","Larry",
           "Moonpig","Norbert","Olivia","Possum","Quentin","Rusty","Scrappy","The Boulder","Umbrella","Venus","Wendy",
           "Yakult","Zanzibar"]
TEST_PLAY_URSELF = False
econv=lambda l:":blue_square:" if l=="*" else ":regional_indicator_%s:" % l.lower()
class bidict(dict):
    def __init__(self, *args, **kwargs):
        super(bidict, self).__init__(*args, **kwargs)
        self.inverse = {}
        for key, value in self.items():
            self.inverse.setdefault(value,[]).append(key)

    def __setitem__(self, key, value):
        if key in self:
            self.inverse[self[key]].remove(key)
        super(bidict, self).__setitem__(key, value)
        self.inverse.setdefault(value,[]).append(key)

    def __delitem__(self, key):
        self.inverse.setdefault(self[key],[]).remove(key)
        if self[key] in self.inverse and not self.inverse[self[key]]:
            del self.inverse[self[key]]
        super(bidict, self).__delitem__(key)

def smart_number(things: list, name: str, plural=None) -> str:
    return "%s %s" % (len(things), name if len(things) == 1 else plural or name + "s")

def smart_list(things: list) -> str:
    if len(things) > 2:
        return "%s and %s" % (", ".join(things[:-1]), things[-1])
    elif len(things) == 2:
        return "%s and %s" % tuple(things)
    return "".join(things)

def thea(name:str,singular:bool) -> str:
    if singular:
        return "the %s" % name
    elif name[0] in "aeiou":
        return "an %s" % name
    return "a %s" % name

def to_emoji(thing)->str:
    if isinstance(thing,int):
        return [":zero:",":one:",":two:",":three:",":four:",":five:",":six:",":seven:",":eight:",":nine:"][thing]
    elif isinstance(thing,str):
        return ":regional_indicator_%s:" % thing.lower()
    return "[ERROR]"
def revolve(l:typing.List):
    if l:
        l.append(l.pop(0))
def assign_letters(players:typing.List[BasePlayer])->dict:
    assignment={}
    remaining = set(string.ascii_uppercase)
    for p in players:
        assigned=p.name[0].upper()
        if assigned not in remaining:
            assigned=random.choice(list(remaining))
        remaining.discard(assigned)
        assignment[p]=assigned
    return assignment

async def gather(coros:typing.List[typing.Coroutine])->typing.List:
    return await asyncio.gather(*coros)

async def smart_gather(coros:typing.List[typing.Coroutine],keys:typing.List)->typing.Dict:
    results=await gather(coros)
    return {k:results[n] for n,k in enumerate(keys)}

async def chain(coros):
    return [await coro for coro in coros]

async def smart_chain(coros:typing.List[typing.Coroutine],keys:typing.List)->typing.Dict:
    results=await chain(coros)
    return {k:results[n] for n,k in enumerate(keys)}
class TextTimer(object):
    msg=None
    RESOLUTION = 1
    paused = False
    def __init__(self,time_remaining:int,channel:discord.TextChannel,message="Time Remaining: %s",interval=10):
        self.time = time_remaining
        self.message = message
        self.interval = interval
        self.channel = channel
    async def run(self,remsg = True):
        if remsg or not self.msg:
            self.msg = await self.channel.send(self.message % self.formatted_time)
        while not self.done:
            await asyncio.sleep(self.RESOLUTION)
            if not self.paused:
                self.time-=self.RESOLUTION
                if not self.time%self.interval:
                    await self.msg.edit(content=self.message % self.formatted_time)
    @property
    def formatted_time(self):
        return f"{self.time//60}:{self.time%60:02d}"
    @property
    def done(self):
        return self.time<=0
class FakeUser(object):
    def __init__(self):
        self.uid=random.randint(0,2**32)
    def update_balance(self,delta):
        return True
    async def dm(self,msg):
        print("%s was DMed %s" % (self.nick,msg))
    def get_elo(self,game):
        return 0
    def set_elo(self,game,new):
        pass
    @property
    def name(self):
        return str(self.uid)
    @property
    def nick(self):
        return fake_names[self.uid%len(fake_names)]
    @property
    def user(self):
        return self
    @property
    def mention(self):
        return "@"+self.nick
class AIUser(object):
    def update_balance(self,delta):
        return True
    async def dm(self,msg):
        pass
    def get_elo(self,game):
        return 100
    def set_elo(self,game,new):
        pass
    @property
    def name(self):
        return "CasinoBot"
    @property
    def nick(self):
        return "CasinoBot"
    @property
    def user(self):
        return self
    @property
    def mention(self):
        return "@"+self.nick
class BasePlayer(object):
    points=0
    busy=False
    def __init__(self,user,fake=False):
        self.user=AIUser() if fake=="ai" else FakeUser() if fake else user
        self.fake=fake
        self.hand=[]
    async def dm(self,msg):
        return await self.user.dm(msg)
    @property
    def name(self):
        return self.user.nick
    @property
    def du(self):
        return self.user.user
    @property
    def dmchannel(self):
        return self.user.dmchannel
    @property
    def tag(self):
        return self.du.mention
class BaseGame(object):
    playerclass=BasePlayer
    started=False
    cost=0
    name=""
    min_players=2
    max_players=10
    done=False
    info={}
    shameable=True
    dunnit = None
    queued=""
    no_pump=True
    has_ai = False
    def __init__(self,ctx):
        self.players=[]
        self.channel=ctx.channel
        self.bot=ctx.bot
    async def join(self, author):
        if isinstance(author,discord.Member):
            user=get_user(author)
            if self.started:
                await self.send("The game has already started!")
                return False
            if any(p.user == user for p in self.players) and not TEST_PLAY_URSELF:
                await self.send("You're already playing!")
                return False
            elif not user.update_balance(-self.cost):
                await self.send("You don't have enough money to play!")
                return False
            else:
                self.players.append(self.playerclass(user))
                await self.send("%s has joined the game! Current players: %s" % (user.nick, len(self.players)))
                return True
        else:
            self.players.append(author)
    async def run(self,*modifiers):
        pass
    async def wait_for_tag(self,choosers,choices):
        return (await self.wait_for_multitag(choosers,choices,1,1))[0]
    async def wait_for_multitag(self,choosers:typing.Union[list,BasePlayer],choices:typing.List[BasePlayer],mn:int,mx:int):
        await self.pump()
        self.dunnit=None
        if choosers is BasePlayer:
            choosers=[choosers]
        if all(c.fake for c in choosers):
            self.dunnit=random.choice(choosers)
            return random.sample(choices,mn)
        for c in choosers:
            c.busy=True
        m = await self.bot.wait_for("message",check=lambda m:m.channel==self.channel and m.author in [c.du for c in choosers] and mn<=len(m.mentions)<=mx and all(u in [c.du for c in choices] for u in m.mentions))
        for c in choosers:
            c.busy = False
            if c.du==m.author:
                self.dunnit=c
        return [c for c in choices if c.du in m.mentions]
    async def dm_tag(self,chooser:BasePlayer,choices:typing.List[BasePlayer],null=False):
        if null:
            await chooser.dm("1: Nobody\n"+"\n".join("%s: %s" % (n+2,c.name) for n,c in enumerate(choices)))
        else:
            await chooser.dm("\n".join("%s: %s" % (n + 1, c.name) for n, c in enumerate(choices)))
        n=await self.choose_number(chooser,True,1,len(choices)+null)
        await chooser.dm("Thanks!")
        return None if n==1 and null else choices[n-1-null]
    async def choose_option(self, player, private, options,msg="Choose an option: ",secret=False):
        if len(options)==1:
            return options[0]
        players=player if isinstance(player,list) else [player]
        if all(p.fake for p in players):
            return random.sample(options,1)[0]
        send = players[0].dm if private else self.send
        option_dict={o.lower():o for o in options}
        if msg:
            if secret:
                await send(msg)
            else:
                await send(msg+", ".join(list(options)))
        tchannel=players[0].dmchannel if private else self.channel
        for p in players:
            p.busy=True
        while True:
            await self.pump()
            chosen = await self.bot.wait_for("message",check=lambda m: m.channel == tchannel and m.author in [p.du for p in players] and m.content)
            if chosen.content.lower() in option_dict:
                for p in players:
                    p.busy = False
                return option_dict[chosen.content.lower()]
            if "$" not in chosen.content:
                await send("Not one of the options...")
    async def smart_options(self,player,private,options,f,msg="Choose an option: ",secret=False):
        def g(o):
            r = f(o)
            return r if isinstance(r,tuple) else (r,)
        choice=await self.choose_option(player,private,sum((g(o) for o in options),()),msg,secret)
        return next(o for o in options if choice in g(o))
    async def yn_option(self,player,private,msg="Do it?"):
        return (await self.choose_option(player,private,["yes","no"],msg,True))=="yes"
    async def choose_number(self, player, private, mn, mx, msg=""):
        return await self.smart_options(player,private,list(range(mn,mx+1)),str,msg,True)
    async def wait_for_shout(self,msg="Speak now: ",valids=None):
        if valids is None:
            valids=self.players
        if all(p.fake for p in self.players):
            return random.choice(valids)
        if msg:
            await self.send(msg)
        vdict={p.du:p for p in valids}
        await self.pump()
        message = await self.bot.wait_for("message",check=lambda m: m.channel == self.channel and m.author in vdict and m.content)
        return vdict[message.author]
    async def wait_for_text(self,player,msg="Type something: ",private=True,validation=lambda t: len(t),confirmation="",faked="poop"):
        players = player if isinstance(player, list) else [player]
        if all(p.fake for p in players):
            return faked
        send = players[0].dm if private else self.send
        if msg:
            await send(msg)
        for p in players:
            p.busy=True
        tchannel = players[0].dmchannel if private else self.channel
        while True:
            await self.pump()
            message = await self.bot.wait_for("message",check=lambda m: m.channel == tchannel and m.author in [p.du for p in players] and m.content)
            if validation(message.content):
                if confirmation:
                    await self.send(confirmation % players[0].name)
                for p in players:
                    p.busy = False
                return message.content
            if "$" not in message.content:
                await tchannel.send("Not a valid option...")
    async def wait_for_picture(self,player,msg="Submit an image: ",private=True):
        if player.fake:
            return "https://hips.hearstapps.com/cosmouk.cdnds.net/15/21/nrm_1432138418-o-poop-emoji-ice-cream-facebook.jpg"
        send = player.dm if private else self.send
        if msg:
            await send(msg)
        tchannel = player.dmchannel if private else self.channel
        player.busy=True
        while True:
            await self.pump()
            message = await self.bot.wait_for("message",check=lambda m: m.channel == tchannel and m.author == player.du and m.attachments)
            u = message.attachments[0].url
            if u[-4:] != ".png":
                await tchannel.send("doesn't look like an image to me...")
            else:
                player.busy=False
                return u
    async def end_game(self,winners,losers=None,draw=False):
        await self.pump()
        if losers is None:
            losers=[p for p in self.players if p not in winners]
        self.done=True
        if winners and losers:
            register_1v1(self.name,[w.user for w in winners],[l.user for l in losers],draw)
            if self.bot:
                await self.bot.get_cog("Economy").elo(self.channel,self.name)
        else:
            await self.send("No elo change - nobody or everybody won!")
        await self.pump()
    async def end_ranked(self,porder:typing.List[typing.List[BasePlayer]]):
        await self.pump()
        self.done=True
        if len(porder)>1:
            register_ranked(self.name,[[p.user for p in ps] for ps in porder])
            if self.bot:
                await self.bot.get_cog("Economy").elo(self.channel,self.name)
        else:
            await self.send("No elo change - nobody or everybody won!")
        await self.pump()
    async def end_points(self):
        points=defaultdict(list)
        for p in self.players:
            points[p.points].append(p)
        await self.end_ranked([points[p] for p in sorted(points.keys(),reverse=True)])
    async def show_scoreboard(self,final=False):
        await self.send(("FINAL SCOREBOARD:\n" if final else "CURRENT SCOREBOARD:\n")+"\n".join("%s: %s" % (p.name,p.points) for p in self.players))
    async def send(self,msg:str="",**kwargs):
        if kwargs or self.no_pump:
            await self.pump()
            await self.channel.send(msg,**kwargs)
        else:
            if len(self.queued+"\n"+msg)>2000:
                self.pump()
                self.queued=msg
            else:
                self.queued+="\n"+msg
    async def pump(self):
        if self.queued:
            await self.channel.send(self.queued)
            self.queued=""
    @property
    def ashamed(self):
        return [p for p in self.players if p.busy]
def inheritors(klass):
    subclasses = set()
    work = [klass]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses
class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.running = {}
        self.game_classes={g.name:g for g in inheritors(BaseGame) if g.name}
    def refresh(self):
        for c, g in list(self.games.items()):
            if g.done:
                self.games.pop(c)
    @commands.command(name="start", help="Start a game in this channel")
    async def start(self,ctx, game:str):
        self.refresh()
        game = game.lower()
        if ctx.channel in self.games:
            await ctx.send("There's already a game of %s in this channel" % self.games[ctx.channel].name)
        else:
            u = get_user(ctx.author)
            u.nick=ctx.author.display_name
            if game in self.game_classes:
                g = self.game_classes[game](ctx)
                self.games[ctx.channel] = g
                if await g.join(ctx.author):
                    await g.pump()
                    return g
                await g.pump()
            else:
                await ctx.send("Game not found: %s" % game)
    @commands.command(name="join", help="Join a game in this channel")
    async def join(self, ctx):
        self.refresh()
        if ctx.channel in self.games:
            u = get_user(ctx.author)
            u.nick=ctx.author.display_name
            success = await self.games[ctx.channel].join(ctx.author)
            await self.games[ctx.channel].pump()
            return success
        else:
            await ctx.send("No games currently in this channel...")

    @commands.command(name="begin", help="Start a game")
    async def begin(self, ctx, *modifiers):
        if ctx.channel in self.games:
            g = self.games[ctx.channel]
            if len(g.players) < g.min_players:
                await ctx.send("Not enough players!")
            elif not g.started:
                g.started=True
                self.running[g]=asyncio.create_task(g.run(*modifiers))
            else:
                await ctx.send("Game already started!")
        else:
            await ctx.send("no game in this channel...")
    @commands.command(name="stop", help="Stop a game")
    async def stop(self,ctx):
        if ctx.channel in self.games:
            g = self.games[ctx.channel]
            if g in self.running:
                self.running[g].cancel()
            del self.games[ctx.channel]
            await ctx.send("The table was flipped and the %s game in this channel ended :cry:" % g.name)
        else:
            await ctx.send("no game in this channel...")
    @commands.command(name="challenge",help="challenge someone to a 2 player game in this channel")
    async def challenge(self,ctx,target:discord.Member,game:str,*modifiers):
        ai=(target==self.bot.user)
        if new_game:=await self.start(ctx, game):
            if ai:
                if new_game.has_ai:
                    if await self.add_ai_player(ctx):
                        await self.begin(ctx,*modifiers)
                    else:
                        await ctx.send("Are _you_ nicknamed CasinoBot???")
                else:
                    await ctx.send("Sorry, I can't play that game yet")
            else:
                await ctx.send("%s, you've been challenged to a game of %s! Type \"yes\" to accept!"  % (target.display_name,game))
                m=await self.bot.wait_for("message",check=lambda m: m.author==target)
                if m.content.lower()=="yes":
                    if await new_game.join(target):
                        await self.begin(ctx,*modifiers)
                    else:
                        await ctx.send("Something went wrong when trying to join the game...")
                        await self.stop(ctx)
                else:
                    await ctx.send(":cry:")
                    await self.stop(ctx)
    @commands.command(name="fake",help="Add a fake player to the current game")
    @commands.is_owner()
    async def add_fake_player(self,ctx,number=1):
        self.refresh()
        for _ in range(number):
            if game:=self.games.get(ctx.channel,None):
                await ctx.send("Fake player added!")
                if number==1:
                    return await game.join(game.playerclass(None, True))
                await game.join(game.playerclass(None, True))
            else:
                await ctx.send("No games currently in this channel...")
    @commands.command(name="ai",help="Adds CasinoBot to the current game")
    async def add_ai_player(self,ctx):
        self.refresh()
        if game:=self.games.get(ctx.channel,None):
            if game.has_ai:
                if not any(p.name=="CasinoBot" for p in game.players):
                    await ctx.send("I joined the game!")
                    await game.join(game.playerclass(None, "ai"))
                    return True
                else:
                    await ctx.send("Either I'm already playing, or someone's impersonating me!")
            else:
                await ctx.send("Sorry, I don't know how to play that game...")
        else:
            await ctx.send("No games currently in this channel...")
    @commands.command(name="games",help="show all current games")
    async def games(self,ctx):
        await ctx.send("Current games: "+", ".join(self.game_classes.keys()))
    @commands.command(name="info",help="Find information about something in the game you're currently playing")
    async def info(self,ctx,*,key):
        key=key.lower()
        if game := self.games.get(ctx.channel, None):
            if key in game.info:
                await ctx.send(game.info[key])
                return
        success=False
        for g in self.game_classes.values():
            if key in g.info:
                await ctx.send(g.info[key])
                success=True
        if not success:
            await ctx.send("No information available on that, sorry.")
    @commands.command(name="who",help="find out who is playing the current game")
    async def who(self,ctx):
        if ctx.channel in self.games:
            g = self.games[ctx.channel]
            await ctx.send("Current players:\n"+"\n".join(p.name for p in g.players))
        else:
            await ctx.send("no game in this channel...")
    @commands.command(name="shame",help="shame those who are taking too long")
    async def shame(self,ctx):
        if ctx.channel in self.games:
            g = self.games[ctx.channel]
            if g.shameable:
                if shame:=g.ashamed:
                    await ctx.send("%s, hurry the fuck up!" % smart_list([p.tag for p in shame]))
                else:
                    await ctx.send("Shame on you, nobody is busy!")
            else:
                await ctx.send("Unfortunately, shaming in this game would reveal too much information...")