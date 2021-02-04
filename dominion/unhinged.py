from .base import *

class PyramidScheme(Action,Attack):
    cost = 3
    desc = "Each opponent must either give you a Copper from their hand, or gain a Copper to their hand if they have no Copper"

class TrueZen(Action):
    desc = "+£5\nTrash your hand"
    override_name = "True Zen"
    cost = 4
    async def play(self,game:Dominion,player:DPlayer):
        player.coins+=5
        game.trash(player,player.hand)
        player.hand.clear()
        player.update_hand()

class VillageIdiot(Action):
    desc = "+1 Card\n+4 Actions\n-1 Action per Action in your hand."
    cost = 2
    override_name = "Village Idiot"
    async def play(self,game:Dominion,player:DPlayer):
        player.draw(1)
        player.actions+=4
        player.actions-=len([c for c in player.hand if "Action" in c.extype])
        player.update_hand()
class QueensCourt(Action):
    cost = 7
    override_name = "Queen's Court"
    desc = "You may play any number of Action cards from your hand twice"
    async def play(self,game:Dominion,player:DPlayer):
        targets = await game.choose_cards(player,[c for c in player.hand if "ACTION" in c.extype],msg="Choose a card to throne.")
        for target in targets:
            await game.play_card(player,target)
            await game.play_card(player,target)
cards = [TrueZen,VillageIdiot,QueensCourt]