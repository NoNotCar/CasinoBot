from mud import TargetedAction,MPlayer,MUD,Action
import mud
import typing
import asyncio

class Shoot(TargetedAction):
    weapon=None
    code = "shoot"
    def exargs_valid(self,game:mud.MUD,player:mud.MPlayer,ex_args:typing.List[str]):
        if player.immobile:
            return "You're too immobilized to aim your weapon atm..."
        if ex_args:
            return "This action takes no additional arguments"
        for i in player.items:
            if hasattr(i,"ammo") and i.ammo>0:
                self.weapon=i
                return True
        return "You have no weapons with ammo!"
    async def execute(self,game:mud.MUD, player:mud.MPlayer):
        self.weapon.ammo-=1
        await game.kill(self.target,"shot")
        await player.dm("BANG! You shot %s!" % self.target.mname)
        await self.notify(player,"shot %s" % self.target.mname,[self.target])

class Taze(TargetedAction):
    code = "taze"
    def exargs_valid(self,game:mud.MUD,player:mud.MPlayer,ex_args:typing.List[str]):
        if player.immobile:
            return "You're too immobilized to taze someone"
        if ex_args:
            return "This action takes no additional arguments"
        return True
    async def execute(self,game:mud.MUD, player:mud.MPlayer):
        self.target.add_temp_condition(mud.Condition.STUNNED,20)
        await player.dm("BZZT! You tazed %s!" % self.target.mname)
        await self.notify(player,"tazed %s" % self.target.mname,[self.target])

class Broadcast(mud.Say):
    code = "broadcast"
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if player.immobile:
            return "You can't hit the broadcast button atm..."
        if player.be(mud.Condition.BLINDED):
            return "You can't see the broadcast button atm..."
        return super().valid(game,player,args)
    async def execute(self, game: mud.MUD, player: mud.MPlayer):
        for p in game.players:
            if p is not player:
                await p.dm('You hear a message over the speakers: "%s"' % self.message)

class Activate(Action):
    code="activate"
    async def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if player.immobile:
            return "You're in no condition to activate anything!"
        if player.be(mud.Condition.BLINDED):
            return "You can't see what you're doing..."
        return super().valid(game, player, args)
    async def execute(self,game:mud.MUD, player:mud.MPlayer):
        if not await player.area.activate(game):
            await player.dm("You hit some switches, but nothing happens...")

class Consume(TargetedAction):
    code="consume"
    speed=30
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if player.immobile:
            return "Can't eat people while immobile!"
        return super().valid(game,player,args)
    async def execute(self,game:MUD, player:MPlayer):
        self.target.add_temp_condition(mud.Condition.RESTRAINED,self.speed+2)
        player.special_desc="%s is trying to eat %s." % (player.mname,self.target.mname)
        await self.notify(player, "is trying to eat %s!" % self.target.mname)
        await asyncio.sleep(self.speed)
        if not player.immobile:
            await game.kill(self.target, "eaten by an imposter", False)
            await player.dm("You successfully ate %s!" % self.target.mname)
            await self.notify(player, "ate %s!" % self.target.mname)
            player.special_desc=""
        else:
            await player.dm("Your feeding was interrupted...")

class Scan(Action):
    code="scan"
    speed=10
    async def execute(self,game:MUD, player:MPlayer):
        player.add_temp_condition(mud.Condition.RESTRAINED,self.speed+2)
        player.special_desc="%s is being scanned." % player.mname
        await self.notify(player,"is scanning themselves.")
        await asyncio.sleep(self.speed)
        if not player.dead:
            await self.notify(player,"is an Impostor!" if player.role.name=="Impostor" else "is not an impostor.")
            player.conditions.append(mud.Condition.SCANNED)
            player.special_desc=""

class Drugs(Action):
    code="drugs"
    async def execute(self,game:MUD, player:MPlayer):
        player.conditions.append(mud.Condition.DRUGGED)
        player.conditions.append(mud.Condition.STUNNED)
        await self.notify(player,"took some drugs.")
        await player.dm("Wow, these drugs are stronger than you thought! You black out...")
        player.special_desc="%s is drugged out on the floor." % player.mname
class Investigate(Action):
    code="investigate"
    async def execute(self,game:mud.MUD, player:mud.MPlayer):
        if hasattr(player.role,"complete"):
            player.role.complete=True
            await player.dm("You've investigated a corpse and found many interesting results!")
    def valid(self,game:mud.MUD, player:mud.MPlayer,args:typing.List[str]):
        if player.area.name!="Morgue":
            return "You need to be in the morgue to investigate bodies!"
        if player.immobile:
            return "You can't investigate bodies while you can't move!"
        if player.be(mud.Condition.BLINDED):
            return "You can't see what you're doing!"
        if any(isinstance(i,mud.Corpse) for i in player.area.entities):
            return True
        return "There aren't any corpses to investigate"

class Cameras(Action):
    code = "cams"
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if player.be(mud.Condition.BLINDED):
            return "You can't see anything, especially camera feeds!"
        return super().valid(game,player,args)
    async def execute(self,game:MUD, player:MPlayer):
        await player.dm("You look through the various camera feeds...")
        await self.notify(player,"is looking at the cameras")
        await asyncio.sleep(10)
        if player.be(mud.Condition.BLINDED):
            await player.dm("You can't see ANYTHING!")
        elif not player.dead:
            await player.dm("\n".join("You can't find %s." % p.mname if p.dead else "%s is in the %s." % (p.mname, p.area.name) for p in game.players if p is not player))


class Note(mud.Item):
    name = "note"
    def __init__(self, message):
        self.desc = "a note reading \"%s\"" % message

class WriteNote(mud.Say):
    code="write"
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if player.immobile:
            return "You can't write notes while immobile!"
        if player.be(mud.Condition.BLINDED):
            return "You can't see what you're writing!"
        return super().valid(game,player,args)
    async def execute(self,game:MUD, player:MPlayer):
        player.area.entities.append(Note(self.message))
        self.notify(player,"dropped a note")

class DnD(Action):
    code="dnd"
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        return "no metagaming!"
