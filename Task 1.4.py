print("Вводите числа большие 0.")
print("0 - окончание ввода.")

list = []
max_el = 0.0
flag = 1
while flag:
    a = float(input())
    if a > 0:
        list.append(a)
        if a > max_el:
            max_el = a
    elif a < 0:
        print("Прочитайте условие, и постарайтесь не повторять такого.")
    else:
        flag = 0

if len(list) == 0:
    print("\nВы не ввели нужные числа.")
else:
    if max_el % 1 == 0:
        d = int(max_el)
        print(f'\nНаибольшее среди всех чисел: {d}.')
    else:
        print(f'\nНаибольшее среди всех чисел: {max_el}.')