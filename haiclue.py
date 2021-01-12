import dib
import word_list
import cards
import random

class WordCard(cards.BaseCard):
    def __init__(self,word):
        self.word=word
    @property
    def text(self):
        return self.word
    @property
    def emoji(self):
        return "[%s]" % self.word
    @property
    def hand_sort(self):
        return self.word
    def __hash__(self):
        return hash(self.word)
word_deck = [WordCard(w) for w in word_list.common]

class Haiclue(cards.CardGame):
    name="haiclue"
    deck = word_deck
    ROUNDS=4
    WORDS=6
    min_players = 2
    def valid_clue(self,text:str,player:cards.Player):
        wset = set([c.text for c in player.hand])
        n=0
        for t in text.split():
            if t in wset:
                wset.remove(t)
                n+=1
            else:
                return False
        return n>1
    async def run(self,*modifiers):
        self.deck=self.deck.copy()
        random.shuffle(self.deck)
        for n in range(self.ROUNDS):
            targets=[self.deck.pop() for _ in range(self.WORDS)]
            await self.send("ROUND %s/%s\nWORDS: " % (n+1,self.ROUNDS)+" ".join(t.emoji for t in targets))
            self.deal(12)
            assigned={p:random.choice(targets) for p in self.players}
            clues=await dib.smart_gather([self.wait_for_text(p,"Your word: %s. Submit your clue!" % assigned[p],True,lambda t,p=p:self.valid_clue(t,p),"%s has submitted their clue!") for p in self.players],
                                         self.players)
            for p in self.players:
                await self.send("%s's clue:\n%s\nGuess the word!" % (p.name,clues[p]))
                guessers=[o for o in self.players if o!=p]
                guesses = await dib.smart_gather([self.smart_options(g,True,targets,lambda t:t.text,"%s's clue:\n%s\nGuess the word!\nOptions: " % (p.name,clues[p])) for g in guessers],guessers)
                correct = [g for (g,guess) in guesses.items() if guess==assigned[p]]
                if correct:
                    await self.send("%s got it right and recieve 1 point! %s recieves %s points! (The word was %s)" % (dib.smart_list([c.name for c in correct]),p.name,len(correct),assigned[p]))
                    for c in correct:
                        c.points+=1
                    p.points+=len(correct)
                else:
                    await self.send("Nobody got it right! No points! The actual word was %s!" % assigned[p])
            await self.show_scoreboard()
        await self.end_points()
