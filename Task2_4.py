import random

print("Введите размерность матрицы: ")
m = int(input())
n = int(input())

matrix = []
vector = []

for i in range(0, m, 1):
    vector.append(random.randint(0, 100))
    matrix_list = []
    for j in range(0, n, 1):
        matrix_list.append(random.randint(0, 100))
    matrix.append(matrix_list)


print(f"\nМатрица и вектор")

for i in range(0, m, 1):
    resalt = "| "
    for j in range(0, n, 1):
        resalt += f"{matrix[i][j]:<4}"
    resalt += f"|   | {vector[i]:<4}|"
    print(resalt)

for i in range(0, m, 1):
    sum_line = 0
    for j in range(0, n, 1):
        sum_line += matrix[i][j] * vector[i]
    vector[i] = sum_line

print(f"\nРезультат умножения")
for i in range(0, m, 1):
    print(f"| {vector[i]:<6}|")
