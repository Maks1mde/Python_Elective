import random

x = int(input("Введите количество чисел: "))
a = []
flag = False

for i in range(0, x, 1):
    y = random.randint(-100, 100)
    a.append(y)
    if flag:
        if y < Min:
            Min = y
        if y > Max:
            Max = y
    else:
        flag = True
        Min = y
        Max = y

print(f"Получившийся список: {a}\n")

for j in range(1, x, 1):
    for i in range(0, x - j, 1):
        if a[i] > a[i + 1]:
            c = a[i + 1]
            a[i + 1] = a[i]
            a[i] = c

print(f"Отсортированный список: {a}\n")

if int(x % 2):
    Median = a[int(x / 2)]
else:
    Median = (a[int(x / 2)] + a[int(x / 2 - 1)]) / 2

print(f"Минимальное значение в списке: {Min}")
print(f"Максимальное значение в списке: {Max}")
print(f"Медиана: {Median}")
