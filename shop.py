import economy
import discord
from discord.ext import commands
shopitems = {}
class ShopItem(object):
    one = False
    desc = "an item you can buy"
    def __init__(self,name:str,cost:int):
        self.cost = cost
        self.name = name
        shopitems[self.name]=self
    async def on_get(self,channel:discord.TextChannel,user:economy.User):
        user.inv[self]+=1
    def __hash__(self):
        return hash(self.name)
    def __eq__(self, other):
        return isinstance(other,ShopItem) and other.name==self.name
    @property
    def display_name(self):
        return self.name.capitalize()
class Modifier(ShopItem):
    one=True
    def __init__(self,name:str,desc:str,cost:int):
        super().__init__(name,cost)
        self.desc=desc
class Token(ShopItem):
    def __init__(self,name:str,desc:str,cost:int):
        super().__init__(name,cost)
        self.desc=desc
class Flair(ShopItem):
    one = True
    def __init__(self,name:str,flair:str,cost:int):
        super().__init__(name,cost)
        self.flair = flair
    async def on_get(self,channel:discord.TextChannel,user:economy.User):
        await super().on_get(channel,user)
        await channel.send(f"Use $flair {self.name} to equip your new flair!")
    @property
    def display_name(self):
        return f"{self.name.capitalize()} [FLAIR]"
    @property
    def desc(self):
        return f"makes your name look like this: {self.flair%'CasinoBot'}"

class IAmRich(ShopItem):
    desc = "gives you a feeling of pride and accomplishment"
    async def on_get(self,channel:discord.TextChannel,user:economy.User):
        await super().on_get(channel,user)
        await user.dm("""I am rich
I deserv it
I am good,
healthy & successful""")
    @property
    def display_name(self):
        return ":gem: I AM RICH :gem:"

class Shop(commands.Cog):
    @commands.command(name="multibuy",help="Buy lots of one item from the shop.")
    async def multibuy(self, ctx:commands.Context, quantity:int,*, thing:str):
        buyer = economy.get_user(ctx.author)
        if quantity<=0:
            await ctx.send("You can't buy less than 1 of something, that's PREPOSTEROUS!")
            return
        if item:=shopitems.get(thing):
            total_q = quantity + buyer.inv[item]
            if item.one and total_q>1:
                await ctx.send("Sorry, you can't have more than one of that.")
                return
            total_cost = quantity * item.cost
            if buyer.update_balance(-total_cost):
                await ctx.send("Buying successful!")
                for _ in range(quantity):
                    await item.on_get(ctx.channel,buyer)
                economy.save()
        else:
            await ctx.send("Sorry, that's not an available item")
    @commands.command(name="buy",help="Buy something from the shop.")
    async def singlebuy(self,ctx:commands.Context,*,thing:str):
        await self.multibuy(ctx,1,thing=thing)
    @commands.command(name="flair",help="Equip a flair you bought.")
    async def flair(self,ctx:commands.Context,*,flair:str):
        user = economy.get_user(ctx.author)
        if flair.lower()=="none":
            user.flair="%s"
            await ctx.send("Removed Flair!")
            economy.save()
            return
        if fitem:=shopitems.get(flair):
            if isinstance(fitem,Flair):
                if user.inv[fitem]:
                    user.flair=fitem.flair
                    await ctx.send(f"Nice look, {user.name}!")
                    economy.save()
                else:
                    await ctx.send("BUY IT FIRST, YOU CHEAPSKATE!")
            else:
                await ctx.send("That's... not a flair.")
        else:
            await ctx.send("That's not even an item in the first place!")
    @commands.command(name="inv",help="View what items you or another player owns.")
    async def inv(self,ctx:commands.Context,other:discord.Member=None):
        target = economy.get_user(other or ctx.author)
        if target.inv:
            await ctx.send(f"{target.name}'s inventory:\n"+"\n".join(f"{i.display_name}: {q}" for i,q in target.inv.items()))
        else:
            await ctx.send(f"{target.name} has no items...")
    @commands.command(name="stock",help="View what items are available at the shop")
    async def stock(self,ctx:commands.Context):
        msg = "CURRENT ITEMS:"
        for s in sorted(shopitems.values(),key=lambda s:s.cost):
            msg+=f"\n{s.display_name} ({s.cost}c): {s.desc}"
        await ctx.send(msg)

Token("name tag","When you shame, Casinobot will use one of these to tag people.",10)
Flair("bugged","@%s :cockroach:",10)
Flair("bold","**%s**",30)
Flair("italic","_%s_",30)
Flair("radioactive",":radioactive:%s:radioactive:",50)
Flair("choochoo",":steam_locomotive::railway_car:[%s]:railway_car::railway_car:",100)
Flair("removed","~~%s~~",150)
Flair("dark side",":waning_gibbous_moon::last_quarter_moon::waning_crescent_moon:(%s):waxing_crescent_moon::first_quarter_moon::waxing_gibbous_moon:",250)
Flair("starstruck",":star: %s :star:",500)
Flair("incognito","||%s||",1000)
Modifier("f-word pass","CasinoBot bothers to be rude when you shame.",1000)
IAmRich("I AM RICH",9999)