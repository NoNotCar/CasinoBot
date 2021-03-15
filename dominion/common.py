from .base import *
import typing
async def cost_limited_gain(game:Dominion,player:DPlayer,max_cost:int,f:typing.Callable[[Card],bool]=lambda c:True,destination="discard"):
    valid = [s.top for c, s in game.supplies.items() if s and s.top.get_cost(game,player) <= max_cost and f(s.top)]
    if valid:
        chosen = await game.choose_card(player, valid, msg=f"Choose a card costing up to {max_cost} to gain!")
        await game.gain(player,chosen.__class__,destination)
        player.update_hand()
        return chosen
    else:
        await player.dm("Wow, there's nothing to gain!")
async def trash_from_hand(game:Dominion,player:DPlayer,mn=0,mx=1):
    to_trash = await game.choose_cards(player, player.hand, mn, mx, "Choose cards to trash!" if mn>0 else "Choose cards to trash, or pass")
    await game.trash(player, to_trash)
    return to_trash
def deck_search(player:DPlayer,f:typing.Callable[[Card],bool]):
    others = []
    while nxt := player.xdraw(1):
        card = nxt[0]
        if f(card):
            return card,others
        else:
            others.append(card)
    return None,others
async def handsize_attack(game:Dominion,target:DPlayer,size:int):
    to_discard = max(0, len(target.hand) - size)
    if to_discard:
        target.discard.dump(await game.choose_cards(target, target.hand, to_discard, to_discard,
                                         f"Choose {to_discard} cards to discard!"))
async def remodel(game:Dominion,player:DPlayer,increase:int,exact=False):
    trashing = await game.choose_card(player, player.hand, msg="Choose a card to trash!")
    if trashing:
        await game.trash(player, trashing)
        target_cost = trashing.get_cost(game, player) + increase
        if exact:
            return await cost_limited_gain(game, player, target_cost,lambda c:c.cost==target_cost)
        return await cost_limited_gain(game, player, target_cost)
class Command(Card):
    def __init__(self):
        super().__init__()
        self.extype = ("COMMAND",) + self.extype