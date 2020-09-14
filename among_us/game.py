import mud
from . import rooms, roles
import random

def shuffled(l:list):
    return random.sample(l,len(l))
class AmongUs(mud.MUD):
    min_players = 3
    max_players = 12
    common_actions = mud.base_actions
    name="amongus"
    round_time = 60
    def create_world(self):
        cabin=rooms.Cabins()
        c_rooms=[cabin]
        for r in shuffled(rooms.all_rooms):
            for br in shuffled(c_rooms):
                for d in shuffled(list(mud.ddict.keys())):
                    if d not in br.links:
                        nr=r()
                        self.link(br,nr,d)
                        c_rooms.append(nr)
                        break
                else:
                    continue
                break
        return cabin
    def get_roles(self):
        imposters=len(self.players)//7+1
        rs=[roles.Impostor]*imposters+[roles.Security]*imposters
        others=[roles.Activist,roles.CEO,roles.Extrovert,roles.Introvert,roles.Coroner]
        random.shuffle(others)
        while len(rs)<len(self.players):
            if others:
                rs.append(others.pop())
            else:
                rs.append(roles.Role)
        return rs

