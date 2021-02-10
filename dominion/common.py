from .base import *
import typing
async def cost_limited_gain(game:Dominion,player:DPlayer,max_cost:int,f:typing.Callable[[Card],bool]=lambda c:True,destination="discard"):
    valid = [s.top for c, s in game.supplies.items() if s and c.cost <= max_cost and f(s.top)]
    if valid:
        chosen = await game.choose_card(player, valid, msg="Choose a card to gain!")
        await game.gain(player,chosen.__class__,destination)
        player.update_hand()
        await game.send(f"{player.name} gained a {chosen.name}!")
        return chosen
    else:
        await player.dm("Wow, there's nothing to gain!")
async def trash_from_hand(game:Dominion,player:DPlayer,mn=0,mx=1):
    to_trash = await game.choose_cards(player, player.hand, mn, mx, "Choose cards to trash!")
    for t in to_trash:
        player.hand.remove(t)
    await game.trash(player, to_trash)
    player.update_hand()
    return to_trash