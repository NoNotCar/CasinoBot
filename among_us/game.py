import mud
from . import rooms, roles
import random

def shuffled(l:list):
    return random.sample(l,len(l))
class bidict(dict):
    def __init__(self, *args, **kwargs):
        super(bidict, self).__init__(*args, **kwargs)
        self.inverse = {}
        for key, value in self.items():
            self.inverse.setdefault(value,[]).append(key)

    def __setitem__(self, key, value):
        if key in self:
            self.inverse[self[key]].remove(key)
        super(bidict, self).__setitem__(key, value)
        self.inverse.setdefault(value,[]).append(key)

    def __delitem__(self, key):
        self.inverse.setdefault(self[key],[]).remove(key)
        if self[key] in self.inverse and not self.inverse[self[key]]:
            del self.inverse[self[key]]
        super(bidict, self).__delitem__(key)
ddict={"east":(1,0),"west":(-1,0),"north":(0,-1),"south":(0,1)}
class AmongUs(mud.MUD):
    min_players = 3
    max_players = 12
    common_actions = mud.base_actions
    name="amongus"
    round_time = 60
    def create_world(self):
        cabin=rooms.Cabins()
        wmap=bidict({(0,0):cabin})
        for r in shuffled(rooms.all_rooms):
            for br in shuffled(list(wmap.values())):
                for d in shuffled(list(mud.ddict.keys())):
                    x,y=wmap.inverse[br][0]
                    tpos=(x+ddict[d][0],y+ddict[d][1])
                    if tpos not in wmap and d not in br.links:
                        nr=r()
                        tx,ty=tpos
                        wmap[tpos]=nr
                        for d2,(dx,dy) in ddict.items():
                            if (tx+dx,ty+dy) in wmap:
                                self.link(nr, wmap[tx+dx,ty+dy], d2)
                        break
                else:
                    continue
                break
        return cabin
    def get_roles(self):
        imposters=len(self.players)//7+1
        rs=[roles.Impostor]*imposters+[roles.Security]*imposters
        others=[roles.Activist,roles.CEO,roles.Extrovert,roles.Introvert,roles.Coroner,roles.Hypochondriac,roles.Submissive]
        random.shuffle(others)
        while len(rs)<len(self.players):
            if others:
                rs.append(others.pop())
            else:
                rs.append(roles.Role)
        return rs

