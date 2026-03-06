# Лабораторная работа №3 ДЕТАЛЬНЫЙ РАЗБОР ВСЕХ ПРАВИЛ
## С кодом и пояснениями



## 1. Основные состояния клеток

```python
# Файл: ForestFireModel, глобальные константы
EMPTY = 0        # Пустая земля
TREE_YOUNG = 1   # Молодое дерево
TREE_MATURE = 2  # Зрелое дерево
TREE_OLD = 3     # Старое дерево
BURNING_LOW = 4  # Слабое горение
BURNING_HIGH = 5 # Сильное горение
WATER = 6        # Вода
ROCK = 7         # Скала
BURNED = 8       # Пепел
GRASS = 9        # Трава
```

---

## 2. Правило: Возгорание дерева от соседей

### Формула
```
Шанс возгорания = prob_spread × (1.0 - (влажность - 0.3) × 0.5) × модификатор_возраста × бонус_соседей
```

### Привязка к коду
Метод: `ForestFireModel.update()` 

```python
# Шаг 1: Определение модификатора по возрасту 
age_modifier = 1.0
if current == TREE_YOUNG:
    age_modifier = 0.7   # молодые труднее загораются
elif current == TREE_OLD:
    age_modifier = 1.4   # старые легче загораются

# Шаг 2: Подсчёт горящих соседей
burning_count = 0
for dy in [-1, 0, 1]:
    for dx in [-1, 0, 1]:
        if dx == 0 and dy == 0:
            continue
        ny, nx = y + dy, x + dx
        if 0 <= ny < self.height and 0 <= nx < self.width:
            if self.grid[ny, nx] in [BURNING_LOW, BURNING_HIGH]:
                burning_count += 1

# Шаг 3: Расчёт итоговой вероятности 
if burning_count > 0:
    moist = self.moisture[y, x]
    # Формула: базовый шанс × влияние влажности × возраст
    spread_prob = prob_spread * (1.0 - (moist - 0.3) * 0.5) * age_modifier
    
    # Бонус за количество горящих соседей
    if burning_count >= 3:
        spread_prob *= 1.5
    
    # Проверка шанса
    if random.random() < spread_prob:
        self.grid[y, x] = BURNING_HIGH if burning_count >= 3 else BURNING_LOW
```

### Пример расчёта
```
Входные данные:
- prob_spread = 0.7
- moisture = 0.6
- дерево зрелое (age_modifier = 1.0)
- burning_count = 2

Расчёт:
1. Влияние влажности: 1.0 - (0.6 - 0.3) * 0.5 = 0.85
2. Базовый шанс: 0.7 * 0.85 * 1.0 = 0.595
3. Бонус соседей: не применяется (2 < 3)
4. Итог: 0.595 (59.5%)

Проверка: random.random() < 0.595 → возгорание
```

---

## 3. Правило: Возгорание от молнии

### Формула
```
Шанс = prob_lightning × модификатор_возраста
```

### Привязка к коду
Метод: `ForestFireModel.update()` 

```python
# Проверка базового шанса молнии
elif random.random() < prob_lightning:
    # Дополнительная проверка с учётом возраста дерева
    if random.random() < age_modifier:
        self.grid[y, x] = BURNING_LOW
```

### Таблица значений
| Возраст | age_modifier | Итоговый шанс при prob_lightning=0.0001 |
|---------|-------------|----------------------------------------|
| Молодое | 0.7 | 0.00007 |
| Зрелое | 1.0 | 0.0001 |
| Старое | 1.4 | 0.00014 |

---

## 4. Правило: Рост и старение деревьев

### Формулы перехода
```
EMPTY → TREE_YOUNG/GRASS:     вероятность = prob_growth
GRASS → TREE_YOUNG:           вероятность = prob_growth × 0.5
TREE_YOUNG → TREE_MATURE:     вероятность = prob_growth × 0.8
TREE_MATURE → TREE_OLD:       вероятность = prob_growth × 0.6
TREE_OLD → EMPTY:             вероятность = prob_growth × 0.05
```

### Привязка к коду
Метод: `ForestFireModel.update()` 

```python
# Механика взросления деревьев 
if current == TREE_YOUNG and random.random() < prob_growth * 0.8:
    self.grid[y, x] = TREE_MATURE
elif current == TREE_MATURE and random.random() < prob_growth * 0.6:
    self.grid[y, x] = TREE_OLD
elif current == TREE_OLD and random.random() < prob_growth * 0.05:
    self.grid[y, x] = EMPTY  # естественная смерть дерева

# Рост на пустой земле 
elif current == EMPTY:
    if random.random() < prob_growth:
        self.grid[y, x] = GRASS if random.random() < 0.3 else TREE_YOUNG

# Превращение травы в дерево 
elif current == GRASS:
    if random.random() < prob_growth * 0.5:
        self.grid[y, x] = TREE_YOUNG
```

---

## 5. Правило: Сгорание и восстановление

### Формулы
```
Горящее дерево → Пепел: вероятность = 0.3 за шаг
Пепел → Пустая земля: после 20 шагов таймера
```

### Привязка к коду
Метод: `ForestFireModel.update()` 

```python
# Обработка горящих клеток 
if current in [BURNING_LOW, BURNING_HIGH]:
    if random.random() < 0.3:  # 30% шанс сгорания за шаг
        self.grid[y, x] = BURNED
        self.burned_timer[y, x] = 20  # установка таймера восстановления

# Восстановление после пожара 
elif current == BURNED:
    self.burned_timer[y, x] -= 1
    if self.burned_timer[y, x] <= 0:
        self.grid[y, x] = EMPTY  # земля готова к новому росту
```

---

## 6. Правило: Генерация ландшафта

### Формула высоты
```
высота = sin(x_norm × 4) × cos(y_norm × 4) × 0.5 + 
         sin(x_norm × 10 + 1) × cos(y_norm × 10) × 0.25 + 
         случайное_значение_от_-0.1_до_0.1
```

### Привязка к коду
Метод: `ForestFireModel.generate_terrain()` 
```python
# Нормализация координат
nx = x / self.width * 4
ny = y / self.height * 4

# Расчёт высоты через комбинацию синусов и косинусов
self.elevation[y, x] = (
    math.sin(nx) * math.cos(ny) * 0.5 +
    math.sin(nx * 2.5 + 1) * math.cos(ny * 2.5) * 0.25 +
    random.uniform(-0.1, 0.1)  # добавление шума
)

# Генерация влажности (строка ~83)
self.moisture[y, x] = random.uniform(0.3, 0.9)
```

### Распределение типов местности
Метод: `ForestFireModel.initialize_forest()` 

```python
if elev < -0.4:
    self.grid[y, x] = WATER  # вода в низинах
elif elev > 0.5 and rand < 0.3:
    self.grid[y, x] = ROCK   # скалы на возвышенностях
elif rand < 0.05:
    self.grid[y, x] = GRASS  # трава
elif rand < 0.65:
    # распределение деревьев с учётом влажности
    ...
```

---

## 7. Правило: Пользовательское взаимодействие

### Добавление воды
Формула проверки круга: `(dx)^2 + (dy)^2 <= radius^2`

Привязка к коду: Метод `ForestFireModel.add_water()` 

```python
def add_water(self, x, y, size=3):
    for dy in range(-size, size + 1):
        for dx in range(-size, size + 1):
            # Проверка попадания в круг
            if dx * dx + dy * dy <= size * size:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    self.grid[ny, nx] = WATER
```

### Тушение пожара
Привязка к коду: Метод `ForestFireModel.extinguish()` 

```python
def extinguish(self, x, y, radius=4):
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    # Тушение только горящих клеток
                    if self.grid[ny, nx] in [BURNING_LOW, BURNING_HIGH]:
                        self.grid[ny, nx] = BURNED
```

---

## 8. Правило: Сбор статистики

### Формулы подсчёта
```
Деревья:  сумма клеток со значениями от 1 до 3
Горящие:  сумма клеток со значениями 4 или 5
Вода:     сумма клеток со значением 6
Трава:    сумма клеток со значением 9
Пепел:    сумма клеток со значением 8
```

### Привязка к коду
Метод: `ForestFireModel.get_stats()` 

```python
def get_stats(self):
    return {
        'trees': int(np.sum((self.grid >= TREE_YOUNG) & (self.grid <= TREE_OLD))),
        'burning': int(np.sum((self.grid == BURNING_LOW) | (self.grid == BURNING_HIGH))),
        'water': int(np.sum(self.grid == WATER)),
        'grass': int(np.sum(self.grid == GRASS)),
        'burned': int(np.sum(self.grid == BURNED)),
    }
```

Обновление интерфейса: Метод `ForestFireApp.update_stats()`

```python
def update_stats(self):
    stats = self.model.get_stats()
    self.stats_labels['generation'].configure(text=f"Поколение: {self.model.generation}")
    self.stats_labels['trees'].configure(text=f"Деревья: {stats['trees']}")
    self.stats_labels['burning'].configure(text=f"Горит: {stats['burning']}")
    # ... остальные метки
```

---

## 9. Сводная таблица правил

| Правило | Условие | Действие | Вероятность | 
|---------|---------|----------|-------------|
| Возгорание от соседа | Горящий сосед + дерево | Дерево загорается | prob_spread × влажность × возраст × соседи | 
| Возгорание от молнии | Случайное событие | Дерево загорается | prob_lightning × возраст | 
| Рост дерева | Пустая клетка | Появление растения | prob_growth | 
| Старение дерева | Текущая стадия + шанс | Переход на следующую стадию | prob_growth × коэффициент |
| Сгорание | Клетка горит | Превращение в пепел | 0.3 | 
| Восстановление | Пепел + таймер = 0 | Превращение в пустую землю | 1.0 |
| Добавление воды | Клик в режиме "вода" | Клетки становятся водой | 1.0 |
| Тушение | Клик в режиме "тушение" | Горящие клетки гаснут | 1.0 | 

---

## 10. Алгоритм одного шага симуляции

```
Метод: ForestFireModel.update()

Для каждой клетки (y, x) сетки:
    1. Получить текущее состояние: current = self.grid[y, x]
    
    2. Обработка по типу состояния:
    
       Если current в [BURNING_LOW, BURNING_HIGH]:
           - С вероятностью 0.3: установить BURNED и таймер = 20
           
       Если current в [TREE_YOUNG, TREE_MATURE, TREE_OLD]:
           - Вычислить age_modifier по возрасту дерева
           - Подсчитать burning_count (горящие соседи)
           - Если burning_count > 0:
               * Вычислить spread_prob по формуле
               * С вероятностью spread_prob: установить BURNING_LOW/HIGH
           - Иначе с вероятностью prob_lightning × age_modifier:
               * Установить BURNING_LOW
           - Обработать переходы между стадиями роста
           
       Если current == EMPTY:
           - С вероятностью prob_growth: создать GRASS или TREE_YOUNG
           
       Если current == BURNED:
           - Уменьшить таймер на 1
           - Если таймер <= 0: установить EMPTY
           
       Если current == GRASS:
           - С вероятностью prob_growth × 0.5: создать TREE_YOUNG
    
    3. Увеличить счётчик поколений: self.generation += 1
```

---

## 11. Настройка параметров симуляции

Параметры задаются в `ForestFireApp.__init__()` 

```python
self.prob_lightning = tk.DoubleVar(value=0.0001)  # шанс молнии за шаг
self.prob_growth = tk.DoubleVar(value=0.01)       # шанс роста растений
self.prob_spread = tk.DoubleVar(value=0.7)        # базовый шанс распространения огня
self.prob_extinguish = tk.DoubleVar(value=0.1)    # зарезервирован
```

Передача параметров в модель: Метод `ForestFireApp.update_simulation()`

```python
self.model.update(
    self.prob_lightning.get(),
    self.prob_growth.get(),
    self.prob_spread.get(),
    self.prob_extinguish.get()
)
```



---

## 12. Заключение

Модель реализует следующие ключевые механизмы:

1. **Вероятностное распространение огня** — формула учитывает влажность, возраст дерева и количество горящих соседей

2. **Возрастная динамика леса** — деревья проходят стадии роста с разными коэффициентами вероятности 

3. **Восстановление экосистемы** — сгоревшие клетки восстанавливаются через фиксированный таймер 

4. **Генерация ландшафта** — высота и влажность определяются математическими функциями от координат 

5. **Интерактивное управление** — пользователь может добавлять воду и тушить пожар кликом мыши 

Все формулы сведены к линейным зависимостям для простоты понимания и настройки. Привязка к конкретным строкам кода позволяет быстро находить и модифицировать нужные правила.

