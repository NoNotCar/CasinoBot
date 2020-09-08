from mud import TargetedAction,MPlayer,MUD,Action
import mud
import typing

class Shoot(mud.TargetedAction):
    weapon=None
    code = "shoot"
    def exargs_valid(self,game:mud.MUD,player:mud.MPlayer,ex_args:typing.List[str]):
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
        await player.dm("BANG! You shot %s!" % player.mname)
        await self.notify(player,"shot %s" % self.target,[self.target])

class Broadcast(mud.Say):
    code = "broadcast"
    async def execute(self, game: mud.MUD, player: mud.MPlayer):
        for p in game.players:
            if p is not player:
                await p.dm('You hear a message over the speakers: "%s"' % self.message)

class Activate(mud.Action):
    code="activate"
    async def execute(self,game:mud.MUD, player:mud.MPlayer):
        if not await player.area.activate(game):
            await player.dm("You hit some switches, but nothing happens...")

class Consume(mud.TargetedAction):
    code="consume"
    free = False
    async def post_execute(self,game:mud.MUD, player:mud.MPlayer):
        if self.target.person in player.area.entities:
            await game.kill(self.target,"eaten by an imposter",False)
            await player.dm("You successfully ate %s!" % self.target.mname)
            await self.notify(player,"ate %s!" % self.target.mname)
        else:
            await player.dm("You tried to eat %s, but they ran away..." % self.target.mname)

class Investigate(mud.Action):
    code="investigate"
    async def execute(self,game:mud.MUD, player:mud.MPlayer):
        if hasattr(player.role,"complete"):
            player.role.complete=True
            await player.dm("You've investigated a corpse and found many interesting results!")
    async def valid(self,game:mud.MUD, player:mud.MPlayer,args:typing.List[str]):
        if player.area.name!="Morgue":
            return "You need to be in the morgue to investigate bodies!"
        if any(isinstance(i,mud.Corpse) for i in player.area.entities):
            return True
        return "There aren't any corpses to investigate"

class Cameras(mud.Action):
    code = "cams"
    free = False
    async def post_execute(self,game:MUD, player:MPlayer):
        await player.dm("\n".join("You can't find %s." % p.mname if p.dead else "%s is in the %s." % (p.mname, p.area.name) for p in game.players if p is not player))
        await self.notify(player,"is looking at the cameras")


class Note(mud.Item):
    name = "note"
    def __init__(self, message):
        self.desc = "a note reading \"%s\"" % message

class WriteNote(mud.Say):
    code="write"
    async def execute(self,game:MUD, player:MPlayer):
        player.area.entities.append(Note(self.message))
        self.notify(player,"dropped a note")

class DnD(mud.Action):
    code="dnd"
    async def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        return "no metagaming!"
