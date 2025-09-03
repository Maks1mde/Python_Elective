result_pattern = "{}*{}={}"

list = []
a = []

for i in range(9):
    a = []
    for j in range(9):
        x = (i+1)*(j+1)
        a.append(x)
    list.append(a)

for i in range(9):
    for j in range(9):
        result_str = result_pattern.format(j+1, i+1, list[i][j])
        print(f'{result_str:<7}', end=" ")
    print()