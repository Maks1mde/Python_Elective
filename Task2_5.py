import random

N = int(input("Введите размерность списка: "))

vector = []

for i in range(0, N, 1):
    vector.append(random.randint(-100, 100))
    while vector[i] == 0:
        vector[i] = random.randint(-100, 100)
    if i == 0 or i == N - 1:
        while vector[i] < 0:
            vector[i] = random.randint(-100, 100)

print(f"Получившийся список: {vector}\n")

for i in range(0, N, 1):
    if vector[i] < 0:
        positive = 0
        j = 0
        while positive == 0:
            if vector[i + j] > 0:
                positive = vector[i + j]
            j += 1
        vector[i] = (positive_main + positive)/2
    else:
        positive_main = vector[i]

print(f"Получившийся список после замен: {vector}")
