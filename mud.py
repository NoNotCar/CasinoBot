import dib
import typing
import random
import asyncio
import enum
base_names=["Anna","Bob","Carl","Doris","Emma","Fred","George","Harry","Iris","John","Kyle","Lily","Matt","Nora",
            "Olly","Paul","Quentin","Ralph","Susan","Tom","Ursa","Val","Wally","Xavier","Yasmin","Zach",
            "Alex","Betty","Carol","Dave","Ed","Faith","Gemma","Hazel","Ingrid","Jade","Karen","Liam","Megan","Ned",
            "Opal","Peggy","Ray","Steve","Tiff","Wendy","Xena","Yoshi","Zara"]
dpairs=[["north","south"],["east","west"]]
ddict={f:s for f,s in dpairs}
ddict.update({s:f for f,s in dpairs})
class Condition(enum.Enum):
    STUNNED=1
    RESTRAINED=2
    BLINDED=3
    SCANNED=4
    DRUGGED=5
class MPlayer(dib.BasePlayer):
    names=base_names
    role=None
    area=None
    dead=False
    person=None
    inv_size=2
    special_desc=""
    def __init__(self,user,fake=False):
        super().__init__(user,fake)
        self.items=[]
        self.conditions=[]
        self.mname=random.choice(self.names)
        self.names.remove(self.mname)
    def add_temp_condition(self,condition:Condition,time:int):
        asyncio.create_task(self._temp_condition(condition,time))
    async def _temp_condition(self,condition:Condition,time:int):
        if condition not in self.conditions:
            await self.dm("You have been %s!" % condition.name.lower())
        self.conditions.append(condition)
        await asyncio.sleep(time)
        self.conditions.remove(condition)
        if condition not in self.conditions and not self.dead:
            await self.dm("You are no longer %s." % condition.name.lower())
    def __del__(self):
        base_names.append(self.mname)
    def be(self,condition:Condition):
        #he really do be stunned
        return condition in self.conditions
    @property
    def immobile(self):
        return self.dead or self.be(Condition.STUNNED) or self.be(Condition.RESTRAINED)
class ActionManager(object):
    def __init__(self,player,game):
        self.player=player
        self.game=game
    async def manage_action_phase(self):
        await self.player.dm("You are %s.\n%s MINUTES REMAIN" % (self.player.mname,self.game.game_length))
        await Look().execute(self.game,self.player)
        while True:
            if self.player.dead:
                return
            actions = self.game.common_actions+self.player.area.special_actions
            if self.player.role:
                actions.extend(self.player.role.special_actions)
            for i in self.player.items:
                actions.extend(i.special_actions)
            adict = {a.code: a() for a in actions}
            m=await self.game.bot.wait_for("message",check=lambda m: m.author==self.player.du and m.channel==self.player.dmchannel and m.content)
            if self.player.dead:
                return
            if self.player.be(Condition.STUNNED):
                await self.player.dm("You're stunned! Can't do anything!")
            else:
                split=[s.lower() for s in m.content.split()]
                if action:=adict.get(split[0],False):
                    err=action.valid(self.game,self.player,split[1:])
                    if err is True:
                        await action.execute(self.game,self.player)
                    else:
                        await self.player.dm(err)
                else:
                    await self.player.dm("Action not found. Valid actions: "+", ".join(adict.keys()))
#Multi-User Dungeons (or, the basis for my new-style games)
class MUD(dib.BaseGame):
    common_actions=[]
    check_time=10
    min_players = 1
    playerclass = MPlayer
    game_length=10
    def __init__(self,ctx):
        super().__init__(ctx)
        self.events=[]
        self.all_areas=set()
    def create_world(self):
        a=Area()
        self.all_areas.add(a)
        return a
    def get_roles(self):
        return [Role for _ in range(self.players)]
    def link(self,link_from,link_to,d:str):
        link_from.links[d]=link_to
        link_to.links[ddict[d]]=link_from
        self.all_areas.add(link_from)
        self.all_areas.add(link_to)
    async def run(self,*modifiers):
        await self.channel.send("Character Assignment:\n"+"\n".join("%s: %s" % (p.name,p.mname) for p in self.players))
        start_area=self.create_world()
        roles=self.get_roles()
        random.shuffle(roles)
        for n,p in enumerate(self.players):
            p.area=start_area
            p.person=Person(p)
            p.role=roles[n]()
        for p in self.players:
            await p.role.on_become(self,p)
            start_area.entities.append(p.person)
        ams = [ActionManager(p, self) for p in self.players]
        tasks = [asyncio.create_task(am.manage_action_phase()) for am in ams]
        for r in range(self.game_length*60//self.check_time):
            await asyncio.sleep(self.check_time)
            if all(p.dead or p.role.did_win(self,p) for p in self.players):
                break
        for t in tasks:
            t.cancel()
        await self.channel.send("GAME OVER!")
        winners=[p for p in self.players if p.role.did_win(self,p)]
        await self.end_game(winners)
        await self.channel.send("THE ROLES:\n"+"\n".join("%s (%s): %s (%s)" % (p.mname,p.name,p.role.name,("won" if p in winners else "lost")) for p in self.players))
    async def kill(self,player:MPlayer,cause="killed",corpse=True):
        player.dead=True
        player.area.entities.remove(player.person)
        if corpse:
            player.area.entities.append(Corpse(player))
            if player.items:
                d=Drop()
                d.items=player.items[:]
                await d.execute(self,player)
        player.area=None
        await player.dm("You were %s!" % cause)
class Area(object):
    special_actions=[]
    name="Area"
    desc="There's nothing special here."
    singular=True
    def __init__(self):
        self.links={}
        self.entities=[]
    def full_desc(self,player:MPlayer):
        desc=self.desc
        if self.items:
            desc+=" There is %s here." % dib.smart_list([i.desc for i in self.items])
        else:
            desc+=" There are no items here."
        if ni:=self.nonitems((player.person,)):
            desc += " %s %s here." % (dib.smart_list([i.desc for i in ni]),("is" if len(ni)<2 else "are"))
            for p in ni:
                if p.player.special_desc:
                    desc+=" %s." % p.player.special_desc
        else:
            desc += " There's nobody else here."
        return desc
    @property
    def items(self):
        return [i for i in self.entities if isinstance(i,Item)]
    def nonitems(self,exclude=()):
        return [i for i in self.entities if not isinstance(i, Item) and i not in exclude]
    def other_people(self,exclude:MPlayer):
        return [i for i in self.entities if isinstance(i,Person) and i.player is not exclude]
class Link(object):
    pass

class Entity(object):
    name="entity"
    desc="an entity"
    async def update(self,game:MUD,area:Area):
        pass
class Person(Entity):
    def __init__(self,player:MPlayer):
        self.player=player
        self.name=player.mname
        self.desc=self.name
class Item(Entity):
    special_actions=[]
    name="item"
    desc="an item"
    heavy=False

class Corpse(Item):
    heavy = True
    name="corpse"
    def __init__(self,player:MPlayer):
        self.player=player
        self.desc="%s's corpse" % self.player.mname
class Action(object):
    code="act"
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if args:
            return "This action takes no arguments"
        return True
    async def execute(self,game:MUD, player:MPlayer):
        pass
    async def notify(self,player:MPlayer,msg="did something.",extra=(),area=None):
        area=area or player.area
        extra=[p.person for p in extra]
        for p in [p for p in area.other_people(player) if p not in extra]:
            await p.player.dm("%s %s" % (player.mname,msg))

class ViewInventory(Action):
    code="inv"
    async def execute(self,game:MUD, player:MPlayer):
        if player.items:
            await player.dm("Your inventory:\n"+"\n".join(i.desc for i in player.items))
        else:
            await player.dm("You don't have any items :cry:")
class Look(Action):
    code="look"
    async def execute(self,game:MUD, player:MPlayer):
        if player.be(Condition.BLINDED):
            await player.dm("You look around and see nothing")
        else:
            await player.dm("You are in %s. %s" % (
            dib.thea(player.area.name, player.area.singular), player.area.full_desc(player)))
class Move(Action):
    code="go"
    direction=None
    speed=10
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if not args:
            return "You have to say a direction to move!"
        if player.immobile:
            return "You can't move!"
        if player.be(Condition.BLINDED):
            return "You can't see where you're going!"
        if len(args)==1:
            self.direction=args[0]
            if self.direction in player.area.links:
                return True
            else:
                return "You can't go that way!"
        return "Too many arguments!"
    async def execute(self,game:MUD, player:MPlayer):
        old_area=player.area
        player.area=None
        old_area.entities.remove(player.person)
        await player.dm("Moving %s..." % self.direction)
        await self.notify(player,"left the room",area=old_area)
        await asyncio.sleep(self.speed)
        player.area = old_area.links[self.direction]
        player.area.entities.append(player.person)
        await self.notify(player, "entered the room")
        await Look().execute(game,player)
class Say(Action):
    code="say"
    message=""
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if args:
            self.message=" ".join(args)
            if len(self.message)>140:
                return "Keep your message shorter than a tweet please :stuck_out_tongue:"
            return True
        return "Say _something_, dammit!"
    async def execute(self,game:MUD, player:MPlayer):
        await self.notify(player,"said \"%s\"" % self.message)
class TargetedAction(Action):
    target=None
    local=True
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if player.be(Condition.BLINDED) and self.local:
            return "You can't see anyone to do that to"
        valid_targets={p.mname:p for p in game.players if p is not player and (not self.local or p.area==player.area)}
        if args:
            tname=args[0].capitalize()
            if tname in valid_targets:
                self.target=valid_targets[tname]
                return self.exargs_valid(game,player,args[1:])
            else:
                return "not a valid target"
        return "please choose a target player for this action"
    def exargs_valid(self,game:MUD,player:MPlayer,ex_args:typing.List[str]):
        if ex_args:
            return "This action doesn't take any more arguments"
        return True

class Whisper(TargetedAction,Say):
    code="whisper"
    def exargs_valid(self,game:MUD,player:MPlayer,ex_args:typing.List[str]):
        return Say.valid(self,game,player,ex_args)
    async def execute(self,game:MUD, player:MPlayer):
        await self.target.dm('%s whispered "%s" to you.' % (player.mname, self.message))
        await self.notify(player,"whispered something",(self.target,))

class Grab(Action):
    code="grab"
    items=None
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if player.immobile:
            return "You can't grab stuff atm."
        if len(args)>player.inv_size-len(player.items):
            return "You can't carry that many items! Drop something first."
        if args:
            self.items=[]
            for a in args:
                for i in player.area.items:
                    if i.name==a and i not in self.items:
                        if i.heavy:
                            return "%s is too heavy to pick up! Try dragging it instead" % i.desc
                        self.items.append(i)
                        break
                else:
                    return "Item not found: %s" % a
            return True
        return "You have to specify an item to grab!"
    async def execute(self,game:MUD, player:MPlayer):
        for i in self.items:
            player.area.entities.remove(i)
            player.items.append(i)
        await self.notify(player,"grabbed %s" % dib.smart_list([i.desc for i in self.items]))

class Drag(Action):
    code="drag"
    direction=None
    old_area=None
    target=None
    speed=20
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if not args:
            return "You have to say a direction to move!"
        if len(args)==1:
            return "You have to specify something to drag!"
        if player.immobile:
            return "You can't move!"
        if player.be(Condition.BLINDED):
            return "You can't see where you're going!"
        if len(args)==2:
            self.direction=args[0]
            if self.direction not in player.area.links:
                return "You can't go that way!"
            target=args[1]
            for i in player.area.items:
                if i.name == target:
                    self.target=i
                    return True
            return "Item not found: %s" % target
        return "Too many arguments!"
    async def execute(self,game:MUD, player:MPlayer):
        moving = [player.person, self.target]
        old_area = player.area
        player.area = None
        for m in moving:
            self.old_area.entities.remove(m)
        await player.dm("Dragging %s %s..." % (self.target.desc,self.direction))
        await self.notify(player, "left the room, dragging %s" % self.target.desc, area=old_area)
        await asyncio.sleep(self.speed)
        player.area = old_area.links[self.direction]
        for m in moving:
            player.area.entities.append(m)
        await self.notify(player, "entered the room, dragging %s" % self.target.desc)
        await Look().execute(game, player)
    async def post_execute(self,game:MUD, player:MPlayer):
        if self.target:
            await self.notify(player,"entered the room, dragging %s" % self.target.desc)
class Drop(Action):
    code="drop"
    items=None
    def valid(self,game:MUD, player:MPlayer,args:typing.List[str]):
        if player.immobile:
            return "You can't drop stuff atm."
        if args:
            self.items=[]
            for a in args:
                for i in player.items:
                    if i.name==a and i not in self.items:
                        self.items.append(i)
                        break
                else:
                    return "Item not found: %s" % a
            return True
        return "You have to specify an item to drop!"
    async def execute(self,game:MUD, player:MPlayer):
        for i in self.items:
            player.items.remove(i)
            player.area.entities.append(i)
        await self.notify(player,"dropped %s" % dib.smart_list([i.desc for i in self.items]))
    
class Event(object):
    async def update(self,game:MUD):
        pass

class Role(object):
    name="Normal Person"
    special_actions=[]
    objective="Survive to the end of the game!"
    singular=False
    async def on_become(self,game:MUD,player:MPlayer):
        await player.dm("You are %s!\n%s" % (dib.thea(self.name,self.singular),self.objective))
    def did_win(self,game:MUD,player:MPlayer):
        return not player.dead

base_actions=[ViewInventory,Move,Grab,Drop,Say,Whisper,Look,Drag]