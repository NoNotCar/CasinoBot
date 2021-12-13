import dib

roles = ["minister","princess","wanderer","priestess"]+["guard"]*4
class Player(object):
    turn = 0
    revealed=False
    captured = False
    protected=False
    def __init__(self,bp:dib.BasePlayer,role:str,name:str):
        self.p=bp
        self.role = role
        self.name=name
class SecretMoon(dib.BaseGame):
    name = "smoon"
    min_players = 5
    max_players = 8
    def __init__(self,ctx):
        super().__init__(ctx)
        self.pidx = {}
        self.discard = []
    async def inspect(self,inspector:dib.BasePlayer,target:int):
        try:
            target = self.pidx[target]
            if target.protected:
                await self.send("Target is protected, can't inspect them!")
            elif target.captured:
                await self.send("Target has been captured, can't inspect them!")
            elif target.revealed:
                await self.send(f"Target has already been revealed to be a {target.role}!")
            else:
                await inspector.dm(f"Target is a {target.role}!")
                return True
        except KeyError:
            await self.send("Invalid Player!")
    async def inquire(self,target:int):
        try:
            target = self.pidx[target]
            if target.protected:
                await self.send("Target is protected, can't inquire!")
            elif target.captured:
                await self.send("Target is captured, can't inquire!")
            elif target.revealed:
                await self.send(f"Target has already been revealed to be a {target.role}!")
            elif target.p:
                response = "You fool! I'm the Minister!" if target.role=="minister" else "..." if target.role in ("princess","wanderer") else "It's just me!"
                await self.send(f'{target.p.name} says: "{response}"')
                return True
            else:
                await self.send("NPCs can't respond!")
        except KeyError:
            await self.send("Invalid Player!")
    async def reveal(self,target:Player):
        if target.revealed:
            await self.send(f"{target.name} has already been revealed!")
            return
        target.revealed=True
        await self.send(f"{target.name} has been revealed to be a {target.role}!")
        if target.role=="guard":
            await self.capture(target)
    async def capture(self,target:Player):
        target.captured=True
        target.turn = 0
        await self.send(f"{target.name} has been captured!")
    async def accuse(self,accuser:dib.BasePlayer,target:int,role:str):
        lrole = role.lower()
        if lrole not in roles:
            await self.send("Invalid role!")
            return
        try:
            target = self.pidx[target]
            if target.protected:
                await self.send("Target is protected, can't accuse them!")
            if target.captured:
                await self.send("Target has already been captured, can't accuse them!")
            elif target.revealed:
                await self.send(f"Target has already been revealed to be a {target.role}!")
            elif target.role==lrole:
                await self.send(f"CORRECT!")
                await self.reveal(target)
                return True
            else:
                await self.send("INCORRECT! You reveal yourself!")
                await self.reveal(self.get_player(accuser))
                return True
        except KeyError:
            await self.send("Invalid Player!")
    async def hide(self,target:int):
        try:
            target = self.pidx[target]
            if target.protected:
                await self.send("Target is already protected!")
            elif target.captured:
                await self.send("You're too late, target has been captured!")
            else:
                target.protected=True
                return True
        except KeyError:
            await self.send("Invalid Player!")
    async def disrupt(self,disruptor:dib.BasePlayer,target:int):
        try:
            target = self.pidx[target]
            if target.protected:
                await self.send("Target has been protected, can't disrupt them!")
            elif target.turn==0:
                await self.send("Target doesn't have a turn order card, can't disrupt them!")
            else:
                await self.send(f"{target.name} has been disrupted and discards their turn order card! {disruptor.name} is captured!")
                await self.capture(self.get_player(disruptor))
                target.turn=0
        except KeyError:
            await self.send("Invalid Player!")
    def get_player(self,bp:dib.BasePlayer)->Player:
        return next(p for p in self.pidx.values() if p.p==bp)

