import discord
from discord.ext import commands
from economy import get_user
import economy
import random
import asyncio
async def wait_for_tag(ctx,player):
    m = await ctx.bot.wait_for("message",check=lambda m: m.author == player.user and len(m.mentions) == 1 and m.mentions[0]!=player.user)
    return get_user(m.mentions[0])
class SlotSymbol(object):
    emoji=":o:"
    value=0
    async def on_triple(self,ctx,player):
        pass
    def __eq__(self, other):
        return isinstance(other,self.__class__)
class Cherry(SlotSymbol):
    emoji = ":cherries:"
    value = 2
    async def on_triple(self,ctx,player):
        await ctx.send(self.emoji*3+" TRIPLE CHERRY! "+self.emoji*3+"\nYou get 50c!")
        player.update_balance(50)
class Morgana(SlotSymbol):
    emoji = ":woman_detective:"
    value = 0
    async def on_triple(self,ctx,player):
        await ctx.send(self.emoji*3+": Choose someone to steal 10c from...")
        while True:
            target=await wait_for_tag(ctx,player)
            if target.update_balance(-10):
                break
            else:
                await ctx.send("%s is TOO POOR. Choose someone else." % target.nick)
        player.update_balance(10)
        await ctx.send("Theft successful!")
class Heart(SlotSymbol):
    emoji = ":heart:"
    value = 1
    async def on_triple(self,ctx,player):
        await ctx.send(self.emoji * 3 + ": Choose someone to share 50c with...")
        target=await wait_for_tag(ctx,player)
        target.update_balance(25)
        player.update_balance(25)
        await ctx.send("Awww, lovely.")
class SuperHeart(SlotSymbol):
    emoji = ":two_hearts:"
    value = 20
    async def on_triple(self,ctx,player):
        await ctx.send(self.emoji * 3 + ": Choose someone to share 100c with...")
        target=await wait_for_tag(ctx,player)
        target.update_balance(50)
        player.update_balance(50)
        await ctx.send("Awww, lovely.")
class Skull(SlotSymbol):
    emoji = ":skull:"
    value = -100
    async def on_triple(self,ctx,player):
        await ctx.send("Unfortunately I can't take your life, but your bank balance will do instead :smiling_imp:")
        player.credits=0
        economy.save()
class Lemon(SlotSymbol):
    emoji = ":lemon:"
    value = -1
    async def on_triple(self,ctx,player):
        if random.randint(0,1):
            await ctx.send("When life gives you lemons, make lemonade! You win 5c.")
            player.update_balance(5)
        else:
            await ctx.send("When life gives you lemons, make life _take the lemons back_. You win nothing.")
class Octopus(SlotSymbol):
    emoji = ":octopus:"
    value = 8
    async def on_triple(self,ctx,player):
        await ctx.send("O C T O P U S\nyou win 88c")
        player.update_balance(88)
class Star(SlotSymbol):
    emoji = ":star:"
    value = 15
    async def on_triple(self,ctx,player):
        await ctx.send("STARSTORM: You get 100c, every other active user gets 10c")
        player.update_balance(90)
        for u in economy.users.values():
            u.update_balance(10)
class Infinity(SlotSymbol):
    emoji = ":infinity:"
    value = 10
    async def on_triple(self,ctx,player):
        await ctx.send("INFINITY: Your balance is set to 9999c")
        player.update_balance(9999-player.credits)
class Stonks(SlotSymbol):
    emoji = ":office_worker:"
    value = 5
    async def on_triple(self,ctx,player):
        await ctx.send("STONKS: Double your money!")
        player.update_balance(player.credits)
class Slots(commands.Cog):
    wheel=[Heart,Cherry,Morgana,Lemon,Skull]*3+[Octopus,Stonks]
    high_stakes_wheel=[SuperHeart,Star,Star,Octopus,Stonks,Infinity,Skull,Skull]
    using=False
    locked_out=None
    def __init__(self, bot):
        self.bot = bot
    @commands.command(help="put money in the slots machine [requires 2c]")
    async def pull(self,ctx,high_stakes=False):
        player=get_user(ctx.author)
        if not high_stakes and player==self.locked_out:
            m = await ctx.send("You're still locked out!")
            await asyncio.sleep(1)
            await m.delete()
            await ctx.message.delete()
            return
        cost=20 if high_stakes else 2
        if self.using:
            m=await ctx.send("Wait for the current player to finish!")
            await asyncio.sleep(1)
            await m.delete()
            await ctx.message.delete()
            return
        if high_stakes and not random.randint(0,9):
            for n in range(4):
                await ctx.send("PULL" if n%2 else "SUPER")
                await asyncio.sleep(1)
        if player.update_balance(-cost):
            self.using=True
            await ctx.send("You put a %s in the machine..." % ("20c note" if high_stakes else "2c coin"))
            slots=await ctx.send(":question:"*3)
            result=[]
            for n in range(3):
                await asyncio.sleep(1)
                result.append(random.choice(self.high_stakes_wheel if high_stakes else self.wheel)())
                await slots.edit(content="".join(s.emoji for s in result)+":question:"*(2-n))
            self.using=False
            if all(r==result[0] for r in result):
                await result[0].on_triple(ctx,player)
            else:
                winnings=sum(s.value for s in result)
                if winnings<=0:
                    if len([s for s in result if isinstance(s,Skull)])==2:
                        await ctx.send("DOUBLE SKULL: You're locked out of playing the normal stakes machine until someone else gets this...")
                        self.locked_out=player
                    else:
                        await ctx.send("Too bad, you didn't win anything")
                else:
                    await ctx.send("You won %sc!" % winnings)
                    player.update_balance(winnings)
        else:
            await ctx.send("You need %s credits to use this slot machine!" % cost)
    @commands.command(name="superpull",help="Use the high stakes machine - big risks, big rewards! [requires 20c]")
    async def super_pull(self,ctx):
        await self.pull(ctx,True)

