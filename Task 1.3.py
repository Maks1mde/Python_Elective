finished_str = "THE NUMBER IS {}! THE GAME IS FINISHED!"
more_str = "THE NUMBER IS MORE THAN {}?"
less_str = "THE NUMBER IS LESS THAN {}?"

print("Введите 2 числа для диапазона: ")

a = int(input())
b = int(input())

print()

if b < a:
    c = a
    a = b
    b = c

flag = 1

while flag:
    if a == b:
        print(finished_str.format(a))
        flag = 0
    else:
        if flag == 1:
            print("1 - да")
            print("0 - нет\n")
            flag = 2

        mid = int((a+b)/2)
        print(more_str.format(mid))
        answer = int(input())
        print()
        if answer:
            a = mid + 1
        else:
            print(less_str.format(mid))
            answer = int(input())
            print()
            if answer:
                b = mid - 1
            else:
                print(finished_str.format(mid))
                flag = 0