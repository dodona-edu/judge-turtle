import turtle as t

n = int(input())
t.pensize(2)
for i in range(n):
    for j in range(4):
        t.forward(20)
        t.left(90)
    t.penup()
    t.forward(25)
    t.pendown()

t.done()
