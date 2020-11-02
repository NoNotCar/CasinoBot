import discord
from discord.ext import commands
from economy import get_user, register_1v1, register_ranked
import asyncio
import random
import trueskill
import typing
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
class FakeUser(object):
    def __init__(self):
        self.uid=random.randint(0,2**32)
    def update_balance(self,delta):
        return True
    async def dm(self,msg):
        print("%s was DMed %s" % (self.nick,msg))
    def get_elo(self,game):
        return trueskill.Rating()
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
class BasePlayer(object):
    points=0
    def __init__(self,user,fake=False):
        self.user=FakeUser() if fake else user
        self.fake=fake
        self.hand=[]
    async def dm(self,msg):
        await self.user.dm(msg)
    @property
    def name(self):
        return self.user.nick
    @property
    def du(self):
        return self.user.user
    @property
    def dmchannel(self):
        return self.user.dmchannel
class BaseGame(object):
    playerclass=BasePlayer
    started=False
    cost=0
    name=""
    min_players=2
    max_players=10
    done=False
    info={}
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
    async def wait_for_tag(self,chooser,choices):
        if chooser.fake:
            return random.sample(choices,1)[0]
        m = await self.bot.wait_for("message",check=lambda m:m.channel==self.channel and m.author == chooser.du and len(m.mentions) == 1 and m.mentions[0] in [c.du for c in choices])
        return next(c for c in choices if c.du==m.mentions[0])
    async def choose_option(self, player, private, options,msg="Choose an option: ",secret=False):
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
        while True:
            chosen = await self.bot.wait_for("message",check=lambda m: m.channel == tchannel and m.author in [p.du for p in players] and m.content)
            if chosen.content.lower() in option_dict:
                return option_dict[chosen.content.lower()]
            if "$" not in chosen.content:
                await send("Not one of the options...")
    async def smart_options(self,player,private,options,f,msg="Choose an option: ",secret=False):
        choice=await self.choose_option(player,private,[f(o) for o in options],msg,secret)
        return next(o for o in options if f(o)==choice)
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
        while True:
            message = await self.bot.wait_for("message",check=lambda m: m.channel == self.channel and m.author in vdict and m.content)
            return vdict[message.author]
    async def wait_for_text(self,player,msg="Type something: ",private=True,validation=lambda t: len(t),confirmation=""):
        if player.fake:
            return "poop"
        send = player.dm if private else self.send
        if msg:
            await send(msg)
        tchannel = player.dmchannel if private else self.channel
        while True:
            message = await self.bot.wait_for("message",check=lambda m: m.channel == tchannel and m.author == player.du and m.content)
            if validation(message.content):
                if confirmation:
                    await self.send(confirmation % player.name)
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
        while True:
            message = await self.bot.wait_for("message",check=lambda m: m.channel == tchannel and m.author == player.du and m.attachments)
            u = message.attachments[0].url
            if u[-4:] != ".png":
                await tchannel.send("doesn't look like an image to me...")
            else:
                return u
    async def end_game(self,winners,losers=None,draw=False):
        if losers is None:
            losers=[p for p in self.players if p not in winners]
        self.done=True
        if winners and losers:
            register_1v1(self.name,[w.user for w in winners],[l.user for l in losers],draw)
            if self.bot:
                await self.bot.get_cog("Economy").elo(self.channel,self.name)
        else:
            await self.send("No elo change - nobody or everybody won!")
    async def end_ranked(self,porder:typing.List[typing.List[BasePlayer]]):
        self.done=True
        if len(porder)>1:
            register_ranked(self.name,[[p.user for p in ps] for ps in porder])
            if self.bot:
                await self.bot.get_cog("Economy").elo(self.channel,self.name)
        else:
            await self.send("No elo change - nobody or everybody won!")
    async def end_points(self):
        points=defaultdict(list)
        for p in self.players:
            points[p.points].append(p)
        await self.end_ranked([points[p] for p in sorted(points.keys(),reverse=True)])
    async def show_scoreboard(self,final=False):
        await self.send(("FINAL SCOREBOARD:\n" if final else "CURRENT SCOREBOARD:\n")+"\n".join("%s: %s" % (p.name,p.points) for p in self.players))
    async def send(self,msg:str):
        await self.channel.send(msg)
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
                    return g
            else:
                await ctx.send("Game not found: %s" % game)
    @commands.command(name="join", help="Join a game in this channel")
    async def join(self, ctx):
        self.refresh()
        if ctx.channel in self.games:
            u = get_user(ctx.author)
            u.nick=ctx.author.display_name
            return await self.games[ctx.channel].join(ctx.author)
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
    async def challenge(self,ctx,target:discord.Member,game:str):
        if new_game:=await self.start(ctx, game):
            await ctx.send("%s, you've been challenged to a game of %s! Type \"yes\" to accept!"  % (target.display_name,game))
            m=await self.bot.wait_for("message",check=lambda m: m.author==target)
            if m.content.lower()=="yes":
                if await new_game.join(target):
                    await self.begin(ctx)
                else:
                    await ctx.send("Something went wrong when trying to join the game...")
                    await self.stop(ctx)
            else:
                await ctx.send(":cry:")
                await self.stop(ctx)
    @commands.command(name="fake",help="Add a fake player to the current game")
    @commands.is_owner()
    async def add_fake_player(self,ctx):
        self.refresh()
        if game:=self.games.get(ctx.channel,None):
            await ctx.send("Fake player added!")
            return await game.join(game.playerclass(None, True))
        else:
            await ctx.send("No games currently in this channel...")
    @commands.command(name="games",help="show all current games")
    async def games(self,ctx):
        await ctx.send("Current games: "+", ".join(self.game_classes.keys()))
    @commands.command(name="info",help="Find information about something in the game you're currently playing")
    async def info(self,ctx,*,key):
        key=key.lower()
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