# Лабораторная работа №3 ДЕТАЛЬНЫЙ РАЗБОР ВСЕХ ПРАВИЛ
## С кодом и пояснениями

---

## ПРАВИЛО 1: Горящая клетка становится пустой (пеплом)

```python
# В методе update() класса ForestFireModel:

if current in [BURNING_LOW, BURNING_HIGH]:
    if random.random() < 0.3:  # 30% шанс сгореть за один кадр
        self.grid[y, x] = BURNED  # Клетка становится пеплом
        self.burned_timer[y, x] = 20  # Таймер восстановления на 20 кадров
```

**Как работает:**
```
Кадр 1:  Горящее дерево
   ↓ (30% шанс)
Кадр 2:  Пепел (таймер = 20)
   ↓ (каждый кадр -1)
Кадр 22:  Пустая земля (таймер = 0)
```

**Почему 30%:** Огонь не сжигает дерево мгновенно, нужно время.

---

## ПРАВИЛО 2: Дерево загорается от соседних горящих клеток

```python
# Подсчёт горящих соседей:
def count_burning_neighbors(self, x, y):
    burning_count = 0
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue  # Не считаем саму клетку
            
            ny, nx = y + dy, x + dx
            if 0 <= ny < self.height and 0 <= nx < self.width:
                if self.grid[ny, nx] in [BURNING_LOW, BURNING_HIGH]:
                    burning_count += 1
    
    return burning_count

# Применение в update():
elif current in [TREE_YOUNG, TREE_MATURE, TREE_OLD]:
    burning_count = self.count_burning_neighbors(x, y)
    
    if burning_count > 0:
        moist = self.moisture[y, x]
        spread_prob = prob_spread * (1.0 - (moist - 0.3) * 0.5)
        
        if burning_count >= 3:
            spread_prob *= 1.5  # Больше соседей = выше шанс
        
        if random.random() < spread_prob:
            self.grid[y, x] = BURNING_HIGH if burning_count >= 3 else BURNING_LOW
```


---

## ПРАВИЛО 3: Молния (спонтанное возгорание)

```python
# В update(), если нет горящих соседей:
elif current in [TREE_YOUNG, TREE_MATURE, TREE_OLD]:
    burning_count = self.count_burning_neighbors(x, y)
    
    if burning_count > 0:
        # ... правило 2 (от соседей)
    
    # ПРАВИЛО 3: Молния
    elif random.random() < prob_lightning:
        self.grid[y, x] = BURNING_LOW
        #                    ^^^^^^^^^^^^
        #              Начинается со слабого горения
```

**Как настроить:**
```python
# В интерфейсе:
self.prob_lightning = tk.DoubleVar(value=0.0001)  # По умолчанию

# Ползунок от 0.0 до 0.01:
('prob_lightning', 'Молния', 0.0, 0.01, 0.0001)
```

**Что означает 0.0001:**
- 0.01% шанс каждый кадр
- На карте 3500 клеток → примерно 1 удар молнии каждые 300 кадров
- При 20 FPS → примерно 1 удар каждые 15 секунд

---

## ПРАВИЛО 4: Рост деревьев на пустых клетках

```python
# В update():
elif current == EMPTY:
    if random.random() < prob_growth:
        self.grid[y, x] = GRASS if random.random() < 0.3 else TREE_YOUNG
        #                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #                    30% трава, 70% молодое дерево

elif current == GRASS:
    if random.random() < prob_growth * 0.5:
        self.grid[y, x] = TREE_YOUNG
        #                    ^^^^^^^^^^^^
        #                    Трава превращается в дерево
```

**Жизненный цикл:**
```
 EMPTY (пустая земля)
   ↓ (prob_growth = 1%)
 GRASS (трава)
   ↓ (prob_growth * 0.5 = 0.5%)
 TREE_YOUNG (молодое дерево)
   ↓ (старение в генерации)
 TREE_MATURE (зрелое дерево)
   ↓
 TREE_OLD (старое дерево)
```

---

## ПРАВИЛО 5: Тушение пожара (ручное)

```python
# Метод тушения в классе ForestFireModel:
def extinguish(self, x, y, radius=4):
    """Тушение пожара в радиусе от клика"""
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            # Проверяем что точка внутри круга:
            if dx*dx + dy*dy <= radius*radius:
                nx, ny = x + dx, y + dy
                
                # Проверка границ карты:
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    # Тушим только горящие клетки:
                    if self.grid[ny, nx] in [BURNING_LOW, BURNING_HIGH]:
                        self.grid[ny, nx] = BURNED
                        #                    ^^^^^
                        #              Превращаем в пепел
```

**Как вызывается:**
```python
# В обработчике клика:
def on_canvas_click(self, event):
    x = event.x // self.cell_size  # Координата X клетки
    y = event.y // self.cell_size  # Координата Y клетки
    
    if 0 <= x < self.model.width and 0 <= y < self.model.height:
        if self.current_mode == 'extinguish':
            self.model.extinguish(x, y, radius=4)  # Вызов тушения
            self.draw_simulation()
            self.update_stats()
```



## ПРАВИЛО 6: Добавление воды (создание барьера)

```python
# Метод добавления воды:
def add_water(self, x, y, size=3):
    """Создание водоёма в месте клика"""
    for dy in range(-size, size + 1):
        for dx in range(-size, size + 1):
            # Круглая форма водоёма:
            if dx*dx + dy*dy <= size*size:
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    self.grid[ny, nx] = WATER
                    #                    ^^^^^
                    #              Любая клетка становится водой
```

**Как работает барьер:**
```python
# В update() НЕТ обработки для WATER:
if current in [BURNING_LOW, BURNING_HIGH]:
    # горит
elif current in [TREE_YOUNG, TREE_MATURE, TREE_OLD]:
    # может загореться
elif current == EMPTY:
    # растёт
# WATER и ROCK просто пропускаются!

# Вода не может загореться → огонь останавливается
```



## ПРАВИЛО 7: Влажность влияет на распространение

```python
# Генерация влажности при создании карты:
def generate_terrain(self):
    for y in range(self.height):
        for x in range(self.width):
            self.moisture[y, x] = random.uniform(0.3, 0.9)
            #                                      ^^^^^^^^^^
            #                            Каждая клетка имеет свою влажность

# Использование в распространении огня:
moist = self.moisture[y, x]  # Получаем влажность клетки
spread_prob = prob_spread * (1.0 - (moist - 0.3) * 0.5)
#                                ^^^^^^^^^^^^^^^^^^^^^^^^
#                      Формула расчёта влияния влажности
```

**Расчёт для разных значений:**

| Влажность | Формула | Итоговый множитель |
|-----------|---------|-------------------|
| 0.3 (сухо) | `1.0 - (0.3 - 0.3) * 0.5` | 1.0 (100%) |
| 0.5 (средне) | `1.0 - (0.5 - 0.3) * 0.5` | 0.9 (90%) |
| 0.7 (влажно) | `1.0 - (0.7 - 0.3) * 0.5` | 0.8 (80%) |
| 0.9 (мокро) | `1.0 - (0.9 - 0.3) * 0.5` | 0.7 (70%) |

**Пример:**
```python
prob_spread = 0.7  # Базовое значение ползунка

# Сухая клетка (0.3):
spread_prob = 0.7 * 1.0 = 0.70  # 70% шанс

# Мокрая клетка (0.9):
spread_prob = 0.7 * 0.7 = 0.49  # 49% шанс
```

---

## ПРАВИЛО 8: Возраст дерева влияет на горение

```python
# При генерации леса:
if moist > 0.7:  # Во влажных местах
    age_rand = random.random()
    if age_rand < 0.3:
        self.grid[y, x] = TREE_YOUNG    # 30% молодые
    elif age_rand < 0.7:
        self.grid[y, x] = TREE_MATURE   # 40% зрелые
    else:
        self.grid[y, x] = TREE_OLD      # 30% старые
else:  # В сухих местах
    self.grid[y, x] = TREE_YOUNG if random.random() < 0.7 else TREE_MATURE
    #                                    ^^^^^^^^^^^^^^^^^^^^
    #                            70% молодые, 30% зрелые, 0% старых

# В сухих местах НЕТ старых деревьев → меньше топлива для огня
```

**Почему так:**
| Тип дерева | Влажность | Горение |
|------------|-----------|---------|
| Молодое | Высокая | Медленное (больше влаги в стволе) |
| Зрелое | Средняя | Нормальное |
| Старое | Низкая | Быстрое (сухая древесина) |

---

## ПРАВИЛО 9: Период восстановления после пожара

```python
# Инициализация таймера:
self.burned_timer = np.zeros((height, width), dtype=np.uint8)

# При сгорании:
if current in [BURNING_LOW, BURNING_HIGH]:
    if random.random() < 0.3:
        self.grid[y, x] = BURNED
        self.burned_timer[y, x] = 20  # 20 кадров

# Восстановление:
elif current == BURNED:
    self.burned_timer[y, x] -= 1  # Уменьшаем каждый кадр
    if self.burned_timer[y, x] <= 0:
        self.grid[y, x] = EMPTY  # Только теперь может расти дерево
```



## ПРАВИЛО 10: Интенсивность огня (слабое/сильное)

```python
# Определение интенсивности:
if burning_count >= 3:
    self.grid[y, x] = BURNING_HIGH  # Сильное горение (красный)
    spread_prob *= 1.5  # Быстрее распространяется
else:
    self.grid[y, x] = BURNING_LOW   # Слабое горение (оранжевый)
```

**Разница:**
| Параметр | BURNING_LOW | BURNING_HIGH |
|----------|-------------|--------------|
| Цвет | Оранжевый | Красный |
| Соседей | 1-2 | 3+ |
| Шанс распространения | Базовый | ×1.5 |
| Визуально | оранжевый | красный |

---

## СВОДНАЯ ТАБЛИЦА ВСЕХ ПРАВИЛ

| № | Правило | Метод/Код | Эффект |
|---|---------|-----------|--------|
| 1 | Сгорание | `if current in [BURNING_LOW, BURNING_HIGH]` | 30% шанс → пепел |
| 2 | От соседей | `count_burning_neighbors()` | 1+ сосед → может загореться |
| 3 | Молния | `random() < prob_lightning` | Случайное возгорание |
| 4 | Рост | `random() < prob_growth` | Пустая → трава/дерево |
| 5 | Тушение | `extinguish(x, y, radius)` | Огонь → пепел |
| 6 | Вода | `add_water(x, y, size)` | Создаёт барьер |
| 7 | Влажность | `(1.0 - (moist - 0.3) * 0.5)` | Замедляет огонь |
| 8 | Возраст | `TREE_YOUNG/MATURE/OLD` | Разная скорость горения |
| 9 | Восстановление | `burned_timer -= 1` | 20 кадров пепла |
| 10 | Интенсивность | `burning_count >= 3` | Слабое/сильное горение |

---



**Каждое правило можно настроить через ползунки или клики!** 🎮


