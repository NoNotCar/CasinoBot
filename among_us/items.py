import mud
import random
from . import actions
class Pistol(mud.Item):
    name = "pistol"
    desc = "a pistol"
    special_actions = [actions.Shoot]
    def __init__(self):
        self.ammo=random.randint(0,6)
class Blaster(mud.Item):
    name="blaster"
    desc="a laser blaster"
    ammo=1
    special_actions = [actions.Shoot]
class Documents(mud.Item):
    name="documents"
    desc="some incriminating documents"
class CaptainLaptop(mud.Item):
    name="laptop"
    desc="the captain's laptop"
    special_actions = [actions.Broadcast,actions.Cameras]
class Paper(mud.Item):
    name="paper"
    desc = "a stack of paper"
    special_actions = [actions.WriteNote]
class Crisps(mud.Item):
    name="crisps"
    desc="a packet of crisps"
class DnD(mud.Item):
    name = "dnd"
    desc = "a DnD starter set"
    special_actions = [actions.DnD]
