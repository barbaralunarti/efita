import random
def generate_cpf():
    d = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        s = sum(x * y for x, y in zip(d, range(len(d) + 1, 1, -1)))
        d.append(0 if s % 11 < 2 else 11 - (s % 11))
    return ''.join(map(str, d))

print(generate_cpf())
