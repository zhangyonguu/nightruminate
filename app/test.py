for number in range(1, 408):
    result = 0
    for digit in str(number):
        result += int(digit) ** 3
    if result == number:
        print(number)