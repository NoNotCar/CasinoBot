import discord
from discord.ext import commands
import math
import pickle
import trueskill
bot = commands.Bot(command_prefix='$')
class User(object):
    credits=10
    dm_channel=None
    elos=None
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
        return self.elos.get(game,trueskill.Rating())
    def set_elo(self,game,rating):
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
        return self.nick
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
def get_user(user: discord.User)-> User:
    try:
        return users[user.id]
    except KeyError:
        users[user.id]=(BankUser if user.bot else User)(user.id,user.display_name)
        return users[user.id]

def register_1v1(game,winners,losers,draw=False):
    new_ratings = trueskill.rate([[w.get_elo(game) for w in winners],[l.get_elo(game) for l in losers]],[0,0] if draw else [0,1])
    for n,w in enumerate(winners):
        w.set_elo(game,new_ratings[0][n])
    for n,l in enumerate(losers):
        l.set_elo(game,new_ratings[1][n])
def register_ranked(game,p_order):
    new_ratings = trueskill.rate([[p.get_elo(game) for p in ps] for ps in p_order],list(range(len(p_order))))
    for n,ps in enumerate(p_order):
        for m,p in enumerate(ps):
            p.set_elo(game,new_ratings[n][m])
class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command(name="balance", help="get your current balance, or view someone else's")
    async def balance(self,ctx, *targets: discord.User):
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
    async def reset(self, ctx, *targets: discord.User):
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
    def format_elo(self,r:trueskill.Rating):
        return int(round(r.mu*4))
    @commands.command(help="get your current elo scores, or the elo for a specific game")
    async def elo(self,ctx,game=""):
        if game:
            scores=[[u,u.get_elo(game)] for u in users.values() if u.elos]
            scores.sort(key=lambda t: t[1],reverse=True)
            if scores:
                await ctx.send("\n".join(["LEADERBOARD FOR %s" % game.upper()]+["%s: %s" % (u.name,self.format_elo(e)) for u,e in scores]))
            else:
                await ctx.send("No scores for this game yet :cry:")
        else:
            user=get_user(ctx.author)
            if user.elos:
                await ctx.send("\n".join(["YOUR SCORES"] + ["%s: %s" % (g, self.format_elo(e)) for g, e in user.elos.items()]))
            else:
                await ctx.send("You haven't played any elo games yet :cry:")
    @commands.is_owner()
    @commands.command(name="test_elo",help="Test the elo system")
    async def test_elo(self,ctx,opponent:discord.User):
        p1=get_user(ctx.author)
        p2=get_user(opponent)
        register_1v1("test",[p1],[p2],False)
    @commands.is_owner()
    @commands.command(name="void_elo",help="Void a user's elo")
    async def void_elo(self,ctx,target:discord.User):
        get_user(target).elos=None
        await ctx.send("%s's elo scores have been ERASED" % target.display_name)
    @commands.is_owner()
    @commands.command(name="nickreset",help="reset everyone's nickname")
    async def nickreset(self,ctx):
        for u in users.values():
            u.nick=u.user.display_name
        await ctx.send("Nicknames reset!")