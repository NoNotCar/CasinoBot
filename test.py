import unittest
import one_word
from secret_hitler import game as shitler
from onenight import game as onenight
from exploding_penguins import game as penguins
import cards
import dib
import telestrations
import turbostrations
import decrypto
import asyncio
import drawful
from avalon import avalon
from mafia import mafia
import forsale
import cockroach

class FakeContext(object):
    bot=None
    async def send(self,message,**kwargs):
        print(message)
    @property
    def channel(self):
        return self
async def test_game(g,players:int,*modifiers):
    game = g(FakeContext())
    for _ in range(players):
        await game.join(game.playerclass(None, True))
    game.started=True
    await asyncio.wait_for(game.run(*modifiers), 10)

class TestOneWord(unittest.IsolatedAsyncioTestCase):
    pass

class TestShitler(unittest.IsolatedAsyncioTestCase):
    async def test_chaos(self):
        await test_game(shitler.Game,10,"farmyard","suicide","anarchy","intrigue","choochoo")
class TestAllGames(unittest.IsolatedAsyncioTestCase):
    games=[
        #drawful.Drawful,
        #avalon.Game,
        #mafia.Mafia,
        # shitler.Game,
        # one_word.OneWord,
        #cards.Hearts,
        #cards.OhHell,
        # telestrations.Telestrations,
        # penguins.Game,
        # turbostrations.Turbostrations,
        #decrypto.Decrypto
        #cards.GreatDalmuti,
        #forsale.ForSale,
        onenight.OneNight,
        cockroach.CockroachPoker
        ]
    async def test_min_players(self):
        for g in self.games:
            with self.subTest(game=g):
                await test_game(g,g.min_players)
    async def test_max_players(self):
        for g in self.games:
            with self.subTest(game=g):
                await test_game(g,g.max_players)


