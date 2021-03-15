import discord
from discord.ext import commands
import math
import pickle
from collections import Counter
bot = commands.Bot(command_prefix='$')
class User(object):
    credits=10
    dm_channel=None
    elos=None
    flair = "%s"
    _inv = None
    def __init__(self,uid,nick):
        self.id=uid
        self.nick=nick
        self.elos={}
    def __hash__(self):
        return self.id
    def __eq__(self, other):
        return isinstance(other,User) and self.id==other.id
    def update_balance(self,delta):
        if delta<0 and self.credits+delta<0:
            return False
        self.credits+=delta
        save()
        return True
    def get_elo(self,game):
        if self.elos is None:
            self.elos={}
        return self.elos.get(game,0)
    def set_elo(self,game,rating):
        last_rating = self.get_elo(game)
        if 100 > last_rating > rating:
            return
        elif last_rating>100>rating:
            rating=100
        self.elos[game]=rating
        save()
    async def dm(self,msg):
        await self.user.create_dm()
        return await self.user.dm_channel.send(msg)
    @property
    def user(self):
        return bot.get_user(self.id)
    @property
    def dmchannel(self):
        return self.user.dm_channel
    @property
    def name(self):
        return self.flair%self.nick
    @property
    def inv(self)->Counter:
        if self._inv is None:
            self._inv=Counter()
        return self._inv
    def has(self,item:str):
        return any(q>0 and i.name==item for i,q in self.inv.items())
    def remove_item(self,item:str,q=1):
        if not self.has(item):
            return False
        item = next(i for i,q in self.inv.items() if i.name==item)
        if self.inv[item]>=q:
            self.inv[item]-=q
            save()
            return True
        return False
class BankUser(User):
    credits = math.inf
    def update_balance(self,delta):
        return True
try:
    with open("users.pickle","rb") as f:
        users=pickle.load(f)
except IOError:
    users={}

def save():
    with open("users.pickle","wb") as f:
        pickle.dump(users,f)
def get_user(user: discord.Member)-> User:
    try:
        return users[user.id]
    except KeyError:
        users[user.id]=(BankUser if user.bot else User)(user.id,user.display_name)
        return users[user.id]
ELO_KEXP = 100
BASE_ELO_WIN = 50
def base_elo_1v1(winner,loser,game):
    return BASE_ELO_WIN*math.exp((loser.get_elo(game)-winner.get_elo(game))/ELO_KEXP)
def single_player_elo_change(p,game,winners,losers):
    if not (winners or losers):
        return 0
    return (sum(base_elo_1v1(p,l,game) for l in losers)-sum(base_elo_1v1(w,p,game) for w in winners))/(len(winners)+len(losers))
def register_1v1(game,winners,losers,draw=False):
    if draw:
        return
    register_ranked(game,[winners,losers])
def register_ranked(game,p_order):
    deltas = [[single_player_elo_change(p,game,sum(p_order[:n],[]),sum(p_order[n+1:],[])) for p in ps] for n,ps in enumerate(p_order)]
    for n,ps in enumerate(p_order):
        for m,p in enumerate(ps):
            p.set_elo(game,max(1,p.get_elo(game)+deltas[n][m]))
class Economy(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    @commands.command(name="balance", help="get your current balance, or view someone else's")
    async def balance(self,ctx, *targets: discord.Member):
        if not targets:
            targets = [ctx.author]
        s = ""
        for t in targets:
            if s:
                s += "\n"
            u = get_user(t)
            c = u.credits
            if c == math.inf:
                c = "infinite"
            s += "%s has %s %s" % (u.nick, c, "credit" if c == 1 else "credits")
        await ctx.send(s)
    @commands.command(name="give", help="give the target user(s) x credits")
    async def give(self,ctx, targets: commands.Greedy[discord.User], x: int):
        if len(targets) == 0:
            await ctx.send("Please specify someone to send money to!")
            return
        if x <= 0:
            await ctx.send("Can't send negative or zero money!")
            return
        if not get_user(ctx.author).update_balance(-x * len(targets)):
            await ctx.send("You don't have enough money to do that!")
            return
        else:
            for u in targets:
                get_user(u).update_balance(x)
                if u == self.bot.user:
                    await ctx.send("Thanks for the gold, kind stranger!")
            await ctx.send("Transaction Successful!")
    @give.error
    async def give_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Give request not parsed... did you tag people incorrectly or try to _split credits_?")
    @commands.command(name="reimburse", help="give the target user(s) x credits from the bank")
    @commands.is_owner()
    async def reimburse(self, ctx, targets: commands.Greedy[discord.User], x: int):
        if len(targets) == 0:
            await ctx.send("Please specify someone to send money to!")
            return
        if x <= 0:
            await ctx.send("Can't send negative or zero money!")
            return
        for u in targets:
            get_user(u).update_balance(x)
        await ctx.send("Transaction Successful!")
    @commands.is_owner()
    @commands.command(name="reset", help="reset your balance, or someone else's")
    async def reset(self, ctx, *targets: discord.Member):
        if not targets:
            targets = [ctx.author]
        for t in targets:
            get_user(t).credits=10
        await ctx.send("Balance(s) reset!")
    @commands.command(name="nick",help="Set your nickname to your current name")
    async def nick(self,ctx):
        new=""
        if len(new)>100:
            await ctx.send("go away dan")
            return
        if new:
            get_user(ctx.author).nick=new
        else:
            get_user(ctx.author).nick=ctx.author.display_name
        await ctx.send("Name set to %s" % get_user(ctx.author).name)
    def format_elo(self,r:float):
        return int(round(r))
    @commands.command(help="get your current elo scores, or the elo for a specific game")
    async def elo(self,ctx,game=""):
        if game:
            scores=[[u,u.get_elo(game)] for u in users.values() if u.elos]
            scores.sort(key=lambda t: t[1],reverse=True)
            if scores:
                await ctx.send("\n".join(["LEADERBOARD FOR %s" % game.upper()]+["%s: %s" % (u.name,self.format_elo(e)) for u,e in scores if e]))
            else:
                await ctx.send("No scores for this game yet :cry:")
        else:
            user=get_user(ctx.author)
            if user.elos:
                await ctx.send("\n".join(["YOUR SCORES"] + ["%s: %s" % (g, self.format_elo(e)) for g, e in user.elos.items() if e]))
            else:
                await ctx.send("You haven't played any elo games yet :cry:")
    @commands.is_owner()
    @commands.command(name="test_elo",help="Test the elo system")
    async def test_elo(self,ctx,opponent:discord.Member):
        p1=get_user(ctx.author)
        p2=get_user(opponent)
        register_1v1("test",[p1],[p2],False)
    @commands.is_owner()
    @commands.command(name="void_elo",help="Void a user's elo")
    async def void_elo(self,ctx,target:discord.Member):
        get_user(target).elos=None
        await ctx.send("%s's elo scores have been ERASED" % target.display_name)
    @commands.is_owner()
    @commands.command(name="reset_elo", help="Reset a game's elo")
    async def void_elo(self, ctx, target: str):
        for u in users.values():
            if u.elos:
                u.set_elo(target,0)
        await ctx.send("%s's elo scores have been RESET" % target)
    @commands.is_owner()
    @commands.command(name="nuke_elo",help="Reset all elos to None")
    async def nuke_elo(self, ctx):
        for u in users.values():
            u.elos=None
        await ctx.send("BOOM!")
    @commands.is_owner()
    @commands.command(name="nickreset",help="reset everyone's nickname")
    async def nickreset(self,ctx):
        for u in users.values():
            u.nick=u.user.display_name
        await ctx.send("Nicknames reset!")
    @commands.is_owner()
    @commands.command(name="nukeinvs",help="reset everyone's inventories")
    async def invreset(self,ctx):
        for u in users.values():
            u._inv=None
        await ctx.send("Inventories reset!")