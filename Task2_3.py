import random

vector1 = []
vector2 = []
vector_sum = []
vector_multi = []

N = int(input("Введите размерность векторов: "))

for i in range(0, N, 1):
    vector1.append(random.randint(0, 100))
    vector2.append(random.randint(0, 100))
    vector_sum.append(vector1[i] + vector2[i])
    vector_multi.append(vector1[i] * vector2[i])

print(f"Вектор 1 | Вектор 2 | Сумма | Произведение")
for i in range(0, N, 1):
    print(f"{vector1[i]:<8} | {vector2[i]:<8} | {vector_sum[i]:<5} | {vector_multi[i]:<12}")

norm1 = 0
norm2 = 0

for i in range(0, N, 1):
    norm1 += vector1[i] ** 2
    norm2 += vector2[i] ** 2

print(f"\nНорма вектора 1: {norm1 ** 0.5:.2f}")
print(f"Норма вектора 2: {norm2 ** 0.5:.2f}\n")

Scal = float(input("Введите скаляр: "))
print(f"\nРезультат умножения вектора на скаляр")

if norm1 > norm2:
    for i in range(0, N, 1):
        vector1[i] *= Scal
        print(f"{vector1[i]:.2f}")
else:
    for i in range(0, N, 1):
        vector2[i] *= Scal
        print(f"{vector2[i]:.2f}")
