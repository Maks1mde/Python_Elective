list = []
a = []
x = 1

for i in range(5):
    a = []
    for j in range(5):
        if ((i+j)%2 == 1):
            a.append(x)
            x += 1
        else:
            a.append("*")
    list.append(a)

for i in range(5):
    for j in range(5):
        print(f'{list[i][j]:<3}', end=" ")
    print()