import dib
from . import cards
import random
import asyncio

class Player(dib.BasePlayer):
    dead=False
    dmchannel=None
    def __init__(self,user,fake=False):
        super().__init__(user,fake)
        self.hand=[]
        self.durations=[]
    async def send_hand(self):
        await self.dm("Your hand: "+", ".join(c.name for c in self.hand))
class Game(dib.BaseGame):
    START_HAND_SIZE=5
    turn=0
    next_turn=None
    playerclass = Player
    deck=None
    discards=None
    max_players = 5
    min_players = 2
    turn_ended=False
    name="penguins"
    info = {c().name.lower():c().full_desc for c in set(cards.basedeck)}
    async def run(self,*modifiers):
        defuse=cards.Defuse
        self.deck=[c() for c in cards.basedeck]
        bombs=[cards.ExplodingPenguin() for _ in self.players] + [c() for c in cards.spbombs]
        for p in self.players:
            p.hand.extend(random.sample(self.deck,self.START_HAND_SIZE))
            for c in p.hand:
                self.deck.remove(c)
            p.hand.append(defuse())
        self.deck.extend(bombs)
        random.shuffle(self.deck)
        random.shuffle(self.players)
        self.discards=[]
        await asyncio.gather(*(p.send_hand() for p in self.players))
        while not self.done:
            await self.run_turn(self.cp)
        if self.survivors:
            await self.channel.send("GAME OVER! %s survived and gets 10c!" % dib.smart_list([s.name for s in self.survivors]))
            for s in self.survivors:
                s.user.update_balance(10)
            await self.end_game(self.survivors)
        else:
            await self.channel.send("GAME OVER! Unfortunately, nobody survived...")
    async def run_turn(self,cp):
        self.next_turn=None
        self.turn_ended=False
        await self.channel.send("It's %s's turn! Current deck size: %s" % (cp.name, len(self.deck)))
        for d in cp.durations:
            await d.start_turn(self)
            if cp.dead:
                await self.move_pointer()
                return
        await cp.send_hand()
        await self.channel.send("Choose actions to play, or pass.")
        while True:
            c=await self.choose_card(cp,[c for c in cp.hand if "ACTION" in c.extype])
            if c:
                await self.channel.send("%s played %s" % (cp.name,c.full_desc))
                cp.hand.remove(c)
                await c.execute(self)
                await self.discard(c)
                if self.turn_ended or self.done:
                    return
                elif cp.dead:
                    if not self.done:
                        await self.move_pointer()
                    return
            else:
                break
        if await self.draw(1,cp):
            await self.end_turn(cp)
        else:
            await self.move_pointer()
    async def kill(self,player):
        player.dead=True
        await self.channel.send("%s has died..." % player.name)
    async def end_turn(self,player=None):
        player = player or self.cp
        if not player.dead:
            for d in player.durations:
                await d.end_turn(self)
                if player.dead:
                    break
        self.turn_ended=True
        await self.move_pointer()
    async def move_pointer(self):
        if self.next_turn and not self.next_turn.dead:
            self.cp = self.next_turn
        else:
            while True:
                self.turn += 1
                self.turn %= len(self.players)
                if not self.cp.dead:
                    break
    async def draw(self,n=1,player=None):
        player=player or self.cp
        for _ in range(n):
            if self.deck:
                top=self.deck.pop(0)
                await self.draw_card(player,top)
                if player.dead:
                    return False
        return True
    async def draw_card(self,player,card):
        if "BOMB" in card.extype:
            await self.channel.send("Bomb drawn!\n" + card.full_desc + "\nYou may play a defuse or pass.")
            c = await self.choose_card(player, [c for c in player.hand if "DEFUSE" in c.extype])
            if c:
                player.hand.remove(c)
                await c.execute(self, card)
            else:
                await card.execute(self)
        else:
            await player.dm("You drew %s" % card.name)
            player.hand.append(card)
    async def discard(self,card):
        self.discards.append(card)
        await card.on_discard(self)

    async def choose_card(self, player, choices, must=False, msg=""):
        valid = [c.name.lower() for c in choices]
        if not must:
            valid.append("pass")
        elif not choices:
            return None
        chosen = await self.choose_option(player,False,valid,msg,True)
        if chosen=="pass":
            return None
        return next(c for c in choices if c.name.lower() == chosen)
    async def choose_number(self, player, private, mn, mx, msg=""):
        return await self.smart_options(player,private,list(range(mn,mx+1)),str,msg,True)
    async def burn(self,player,msg="%s is on fire! Choose a card to discard."):
        if player.hand:
            await self.channel.send(msg % player.name)
            c = await self.choose_card(player, player.hand, True)
            player.hand.remove(c)
            await self.discard(c)
            return True
        else:
            await self.channel.send("You have no cards to discard...")
            return False
    @property
    def cp(self):
        return self.players[self.turn] if self.players else None
    @cp.setter
    def cp(self,value):
        self.turn=self.players.index(value)
    @property
    def survivors(self):
        s=[]
        for n,_ in enumerate(self.players):
            p=self.players[(self.turn+n)%len(self.players)]
            if not p.dead:
                s.append(p)
        return s
    @property
    def done(self):
        return self.started and (len(self.survivors)<2 or not self.deck)
    @done.setter
    def done(self,new):
        pass