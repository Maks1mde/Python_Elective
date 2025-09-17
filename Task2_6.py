import random

N = int(input("Введите размерность массива данных: "))
N_1 = int(input("Введите размерность ядра фильтра: "))

vector = []
kernel = []

for i in range(0, N, 1):
    vector.append(random.randint(-10, 10))

for i in range(0, N_1, 1):
    kernel.append(random.randint(-10, 10))

print(f"\nМассива данных: {vector}")
print(f"Ядро фильтра: {kernel}\n")

result = []

if N_1 > N:
    print("Ошибка: фильтр имеет большую размерность")
else:
    for i in range(0, N-N_1+1, 1):
        result.append(0)
        for j in range(0, N_1, 1):
            result[i] += vector[i+j] * kernel[j]

print(f"Получившийся список после замен: {result}")
