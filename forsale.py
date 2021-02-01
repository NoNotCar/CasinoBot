import dib
import random
from collections import defaultdict
real_estate = ["Cardboard Box","Portaloo","Doorway","Kennel","Cave","Bivouac",
               "Teepee","Igloo","Shack","Hut","Treehouse","Car",
               "Bunker","Caravan","Log Cabin","Hill Fort","Narrowboat","Motorhome",
               "Apartment","Terrace","Bungalow","Cottage","Big House","Private Island",
               "Village","Manor","Mansion","Palace","Skyscraper","Space Station"]
def card_text(n:int):
    return "%s: %s" % (n,real_estate[n-1])
sales = [0]*2+list(range(2,16))*2
class FSPlayer(dib.BasePlayer):
    points = 16
    def __init__(self,p,f=False):
        super().__init__(p,f)
        self.bought = []
def rank(n:int,l:list):
    return sorted(l).index(n)

class ForSale(dib.BaseGame):
    name="forsale"
    max_players = 6
    min_players = 3
    playerclass = FSPlayer
    async def run(self,*modifiers):
        estates = list(range(1,31))
        random.shuffle(estates)
        while len(estates)%len(self.players):
            estates.pop()
        turn = 0
        random.shuffle(self.players)
        while estates:
            bids = {p:0 for p in self.players}
            available = [estates.pop() for _ in enumerate(self.players)]
            available.sort()
            await self.send("NEW PROPERTIES ON THE MARKET: "+", ".join(card_text(a) for a in available))
            out = []
            while len(out)<len(self.players)-1:
                cp = self.players[turn]
                passed = cp.points<=max(bids.values())
                while not passed:
                    nbid = await self.choose_number(cp,False,0,cp.points,"%s, choose how much to bid, or pass by bidding 0. (Your current bid: %s)" % (cp.tag,bids[cp]))
                    if nbid==0:
                        passed=True
                    elif nbid>max(bids.values()):
                        bids[cp]=nbid
                        break
                    else:
                        await self.send("You have to beat the current max bid of %s!" % max(bids.values()))
                if passed:
                    await self.send("%s passed and gets %s for £%sk!" % (cp.name,card_text(available[len(out)]),(bids[cp]+1)//2))
                    out.append(cp)
                turn+=1
                turn%=len(self.players)
                while self.players[turn] in out:
                    turn += 1
                    turn %= len(self.players)
            winner = self.players[turn]
            await self.send("%s won the auction and gets %s for £%sk!" % (winner.name,card_text(available[-1]),bids[winner]))
            for n,p in enumerate(out+[winner]):
                cost = bids[p] if p is winner else (bids[p]+1)//2
                p.points-=cost
                p.bought.append(available[n])
                if cost:
                    await p.dm("You now have £%sk left!" % p.points)

        await self.send("THE PROPERTY BUYING PHASE HAS ENDED!")
        asales = sales[:]
        random.shuffle(asales)
        while self.players[0].bought:
            prices = []
            while len(prices)<len(self.players):
                prices.append(asales.pop())
            prices.sort()
            await self.send("TIME TO SELL SOME PROPERTY! Current prices: "+ ", ".join("£%sk" % p for p in prices))
            choices = await dib.gather([self.smart_options(p,True,p.bought,str,"Choose a property to sell! Options: "+", ".join(card_text(b) for b in p.bought)) for p in self.players])
            for n,p in enumerate(self.players):
                sold = choices[n]
                earnings = prices[rank(sold,choices)]
                await self.send("%s sold %s for £%sk!" % (p.name,card_text(sold),earnings))
                p.bought.remove(sold)
                p.points+=earnings
        await self.show_scoreboard(True)
        await self.end_points()


