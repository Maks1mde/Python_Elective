import random

a = []
result = [0] * 10

for i in range(0, 20, 1):
    y = random.randint(0, 99)
    a.append(y)
    j = int(y / 10)
    result[j] += 1

print(f"Получившийся список: {a}\n")

for i in range(0, 10, 1):
    result_text = f"Бин [{int(i * 10)}-{int(i * 10 + 9)}]: "
    print(f"{result_text:>13}{result[i]}")

print()

for i in range(0, 10, 1):
    result_text = f"Бин [{int(i * 10)}-{int(i * 10 + 9)}]: "
    print(f"{result_text:>13}{int(result[i] / 20 * 100)}%")
