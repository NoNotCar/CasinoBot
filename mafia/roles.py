import random
class Role(object):
    evil = False
    true_name = "Role"
    emoji = ":stuck_out_tongue:"
    help = "???"
    singular = False
    night_phases=[]

    def __init__(self, player):
        self.player = player

    async def on_become(self):
        await self.player.dm("You are %s!" % self.name)
        await self.player.dm(self.help)

    async def on_game_start(self, game):
        if self.evil:
            await self.player.dm("Your fellow evildoers are: " + " ".join(
                p.name for p in game.players if p.role.known_to_evil and p is not self.player))

    async def night_phase(self, game, phase):
        pass
    async def on_death(self,game):
        pass
    async def on_attack(self,game):
        return not self.player.healed
    async def cleanup(self,game):
        pass
    def did_win(self, game, evil_wins):
        return self.evil == evil_wins

    @classmethod
    def random_valid(cls, other_roles):
        return not (cls.singular and cls in other_roles)

    @property
    def name(self):
        return self.true_name + " " + self.emoji

    @property
    def appears_evil(self):
        return self.evil

    @property
    def known_to_evil(self):
        return self.evil
class Mafia(Role):
    evil = True
    true_name = "Mafia"
    emoji = ":spy:"
    boss=False
    killed=None
    night_phases = [1,2]
    help = "Pretend to be innocent while killing the villagers at night!"
    async def night_phase(self, game, phase):
        if phase==1:
            if not self.boss and not any(p.role.boss for p in game.alive if isinstance(p.role,Mafia)):
                self.boss=True
                await self.player.dm("After the tragic demise of your predecessor, you have been made boss.")
            if self.boss:
                await self.player.dm("You are the boss. Choose somebody to kill!")
                target = await game.dm_tag(self.player,[p for p in game.alive if not p.role.known_to_evil])
                target.attacked=True
                self.killed=target
        elif phase==2 and not self.boss:
            boss = next(p for p in game.alive if isinstance(p.role,Mafia) and p.role.boss)
            await self.player.dm("The mafia boss, %s, decided to kill %s" % (boss.name,boss.role.killed.name))
class Dentist(Mafia):
    true_name = "Dentist"
    emoji = ":tooth:"
    night_phases = [1,2,3]
    help = "You're a member of the mafia, but can also use your _unique_ talents to shut people up!"
    last_muted=None
    singular = True
    async def night_phase(self, game, phase):
        if phase==3:
            await self.cleanup(game)
            await self.player.dm("Choose someone to mute!")
            target = await game.dm_tag(self.player,game.alive,True)
            if target:
                await target.dm("You've been muted by The Dentist!")
                if not target.fake:
                    await target.du.edit(mute=True)
                    self.last_muted=target
    async def cleanup(self,game):
        if self.last_muted:
            await self.last_muted.dm("You have healed up and can speak again!")
            await self.last_muted.du.edit(mute=False)
    async def on_death(self,game):
        await self.cleanup(game)
class Doctor(Role):
    true_name = "Doctor"
    emoji = ":ambulance:"
    night_phases = [1]
    healed_self=False
    singular = True
    help = "You can prevent people from dying, but can only use this on yourself once."
    async def night_phase(self, game, phase):
        valids = [p for p in game.alive if p!=self.player or not self.healed_self]
        await self.player.dm("Choose someone to heal!")
        target = await game.dm_tag(self.player,valids)
        target.healed=True
        if target==self.player:
            self.healed_self=True
class PlagueDoctor(Role):
    true_name = "Plague Doctor"
    emoji = ":microbe:"
    night_phases = [2]
    singular = True
    help = "You can prevent other people from dying through the power of bloodletting, but this kills people who weren't attacked..."
    async def night_phase(self, game, phase):
        valids = [p for p in game.alive if p!=self.player]
        await self.player.dm("Choose someone to \"heal\"!")
        target = await game.dm_tag(self.player,valids)
        if target.attacked:
            target.healed=True
        else:
            target.attacked=True
class Investigator(Role):
    true_name = "Investigator"
    emoji = ":mag:"
    night_phases = [1]
    help = "You can investigate one person each night, and determine if they're evil!"
    singular = True
    async def night_phase(self, game, phase):
        await self.player.dm("Choose someone to investigate!")
        target = await game.dm_tag(self.player,game.alive)
        if target.role.appears_evil:
            await self.player.dm("%s appears to be evil!" % target.name)
        else:
            await self.player.dm("%s appears to be good!" % target.name)
class PrivateInvestigator(Role):
    true_name = "Private Investigator"
    emoji = ":technologist:"
    night_phases = [1]
    help = "With the power of the internet, you can precisely determine one person's role. Choose when to use this carefully!"
    used=False
    singular = True
    async def night_phase(self, game, phase):
        if not self.used:
            await self.player.dm("You may choose someone to investigate.")
            target = await game.dm_tag(self.player,game.alive,True)
            if target:
                self.used=True
                await self.player.dm("%s is a %s!" % (target.name,target.role.name))
class Villager(Role):
    true_name = "Villager"
    emoji = ":slight_smile:"
    help = "You're a very boring person."
class Tanner(Role):
    true_name = "Tanner"
    emoji = ":poop:"
    help = "You want to die!"
    singular = True
    def did_win(self, game, evil_wins):
        return self.player.dead
class ToughGuy(Role):
    true_name = "Tough Guy"
    emoji = ":mechanical_arm:"
    help = "You can survive one attack before dying!"
    hit=False
    singular = True
    async def on_attack(self,game):
        if not self.hit and not self.player.healed:
            self.hit=True
            await self.player.dm("You have been shot! Don't let it happen again!")
            return False
        return await super().on_attack(game)
class Lover(Role):
    true_name = "Lover"
    emoji = ":heart_eyes:"
    help = "A star-crossed lover, you win if either you and your soulmate both live or both die. You can also send heartfelt letters to them during the night."
    lover=None
    night_phases = [1]
    async def on_game_start(self, game):
        self.lover=random.choice([p for p in game.players if p!=self.player])
        await self.player.dm("Your soulmate is %s!" % self.lover.name)
    async def night_phase(self, game, phase):
        letter = await game.wait_for_text(self.player,"Pen your sweet love letter to your soulmate!",confirmation="Thanks!")
        await self.lover.dm("You have received a sweetly scented letter! It reads:\n"+letter)
    def did_win(self, game, evil_wins):
        return self.player.dead==self.lover.dead
all_roles = [Mafia,Doctor,Villager,Investigator,Tanner,PrivateInvestigator,ToughGuy,PlagueDoctor,Lover]
evils = [r for r in all_roles if r.evil]
goods = [r for r in all_roles if not r.evil]