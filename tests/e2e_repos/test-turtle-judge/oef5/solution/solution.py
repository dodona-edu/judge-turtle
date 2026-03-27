import turtle as t

n = int(input())
for i in range(n):
    t.forward(50)
    t.left(360 / n)

t.done()
