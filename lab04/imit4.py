import random
import numpy as np


class LCG:
    def __init__(self, seed=42):
        self.state = seed
        self.m = 2**32
        self.a = 1664525
        self.c = 1

    def next(self):
        self.state = (self.a * self.state + self.c) % self.m
        return self.state / self.m


N = 100000  # Размер выборки
lcg = LCG(seed=52)

# Генерация выборок
custom_sample = [lcg.next() for _ in range(N)]
builtin_sample = [random.random() for _ in range(N)] #



#  Вычисление статистик
def get_stats(sample):
    mean = np.mean(sample)
    variance = np.var(sample)
    return mean, variance

mean_custom, var_custom = get_stats(custom_sample)
mean_builtin, var_builtin = get_stats(builtin_sample)

# Теоретические значения
theoretical_mean = 0.5
theoretical_var = 1/12

# Вывод результатов
print(f"{'Параметр':<20} | {'Теория':<10} | {'Собственный БД':<15} | {'Встроенный БД'}")
print("-" * 70)
print(f"{'Среднее (Mean)':<20} | {theoretical_mean:<10.5f} | {mean_custom:<15.5f} | {mean_builtin:.5f}")
print(f"{'Дисперсия (Var)':<20} | {theoretical_var:<10.5f} | {var_custom:<15.5f} | {var_builtin:.5f}")
