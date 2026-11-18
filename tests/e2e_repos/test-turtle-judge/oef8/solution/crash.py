import turtle as t

colour = input()
if colour == "blue":
    raise ValueError(colour)
t.pensize(2)
t.pencolor(colour)
for i in range(4):
    t.forward(40)
    t.left(90)

t.done()
