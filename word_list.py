import string
with open("words.txt","r") as f:
    words=set(w.strip() for w in f.readlines() if all(l in string.ascii_lowercase for l in w.strip()))
with open("30k.txt", "r") as f:
    common=set(w.strip() for w in f.readlines() if w.strip() in words)
ldist=list("e"*12+"ai"*9+"o"*8+"nrt"*6+"lsud"*4+"g"*3+"bcmpfhvwy"*2+"kjqxz"*1)