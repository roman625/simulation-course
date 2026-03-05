import tkinter as tk
from tkinter import ttk
import numpy as np
import random
import math

# ============================================================================
# КОНСТАНТЫ
# ============================================================================

# Состояния клеток
EMPTY = 0
TREE_YOUNG = 1
TREE_MATURE = 2
TREE_OLD = 3
BURNING_LOW = 4
BURNING_HIGH = 5
WATER = 6
ROCK = 7
BURNED = 8
GRASS = 9

# Цвета (RGB)
COLORS = [
    (210, 180, 140),  # EMPTY
    (143, 188, 143),  # TREE_YOUNG
    (34, 139, 34),  # TREE_MATURE
    (0, 100, 0),  # TREE_OLD
    (255, 165, 0),  # BURNING_LOW
    (220, 20, 60),  # BURNING_HIGH
    (30, 144, 255),  # WATER
    (128, 128, 128),  # ROCK
    (69, 69, 69),  # BURNED
    (124, 252, 0),  # GRASS
]


class ForestFireModel:
    """Модель лесного пожара"""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = np.zeros((height, width), dtype=np.uint8)
        self.elevation = np.zeros((height, width))
        self.moisture = np.zeros((height, width))
        self.burned_timer = np.zeros((height, width), dtype=np.uint8)
        self.generation = 0

    def generate_terrain(self):
        """Генерация ландшафта"""
        for y in range(self.height):
            for x in range(self.width):
                nx = x / self.width * 4
                ny = y / self.height * 4
                self.elevation[y, x] = (
                        math.sin(nx) * math.cos(ny) * 0.5 +
                        math.sin(nx * 2.5 + 1) * math.cos(ny * 2.5) * 0.25 +
                        random.uniform(-0.1, 0.1)
                )
                self.moisture[y, x] = random.uniform(0.3, 0.9)

    def initialize_forest(self):
        """Инициализация леса"""
        self.generate_terrain()

        for y in range(self.height):
            for x in range(self.width):
                elev = self.elevation[y, x]
                moist = self.moisture[y, x]
                rand = random.random()

                if elev < -0.4:
                    self.grid[y, x] = WATER
                elif elev > 0.5 and rand < 0.3:
                    self.grid[y, x] = ROCK
                elif rand < 0.05:
                    self.grid[y, x] = GRASS
                elif rand < 0.65:
                    if moist > 0.7:
                        age_rand = random.random()
                        if age_rand < 0.3:
                            self.grid[y, x] = TREE_YOUNG
                        elif age_rand < 0.7:
                            self.grid[y, x] = TREE_MATURE
                        else:
                            self.grid[y, x] = TREE_OLD
                    else:
                        self.grid[y, x] = TREE_YOUNG if random.random() < 0.7 else TREE_MATURE
                else:
                    self.grid[y, x] = EMPTY

    def update(self, prob_lightning, prob_growth, prob_spread, prob_extinguish):
        """Обновление модели"""
        for y in range(self.height):
            for x in range(self.width):
                current = self.grid[y, x]

                if current in [BURNING_LOW, BURNING_HIGH]:
                    if random.random() < 0.3:
                        self.grid[y, x] = BURNED
                        self.burned_timer[y, x] = 20

                elif current in [TREE_YOUNG, TREE_MATURE, TREE_OLD]:
                    burning_count = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < self.height and 0 <= nx < self.width:
                                if self.grid[ny, nx] in [BURNING_LOW, BURNING_HIGH]:
                                    burning_count += 1

                    if burning_count > 0:
                        moist = self.moisture[y, x]
                        spread_prob = prob_spread * (1.0 - (moist - 0.3) * 0.5)
                        if burning_count >= 3:
                            spread_prob *= 1.5

                        if random.random() < spread_prob:
                            self.grid[y, x] = BURNING_HIGH if burning_count >= 3 else BURNING_LOW

                    elif random.random() < prob_lightning:
                        self.grid[y, x] = BURNING_LOW

                elif current == EMPTY:
                    if random.random() < prob_growth:
                        self.grid[y, x] = GRASS if random.random() < 0.3 else TREE_YOUNG

                elif current == BURNED:
                    self.burned_timer[y, x] -= 1
                    if self.burned_timer[y, x] <= 0:
                        self.grid[y, x] = EMPTY

                elif current == GRASS:
                    if random.random() < prob_growth * 0.5:
                        self.grid[y, x] = TREE_YOUNG

        self.generation += 1

    def get_stats(self):
        """Получение статистики"""
        return {
            'trees': int(np.sum((self.grid >= TREE_YOUNG) & (self.grid <= TREE_OLD))),
            'burning': int(np.sum((self.grid == BURNING_LOW) | (self.grid == BURNING_HIGH))),
            'water': int(np.sum(self.grid == WATER)),
            'grass': int(np.sum(self.grid == GRASS)),
            'burned': int(np.sum(self.grid == BURNED)),
        }

    def add_water(self, x, y, size=3):
        """Добавление воды - ИСПРАВЛЕНО"""
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                if dx * dx + dy * dy <= size * size:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        self.grid[ny, nx] = WATER

    def extinguish(self, x, y, radius=4):
        """Тушение пожара - ИСПРАВЛЕНО"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.grid[ny, nx] in [BURNING_LOW, BURNING_HIGH]:
                            self.grid[ny, nx] = BURNED


class ForestFireApp:
    """Приложение"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Моделирование лесных пожаров")
        self.root.configure(bg='#1a1a2e')
        self.root.resizable(False, False)

        # Параметры
        self.cell_size = 6
        self.grid_width = 70
        self.grid_height = 50
        self.fps = 20

        # Модель
        self.model = ForestFireModel(self.grid_width, self.grid_height)
        self.model.initialize_forest()

        # Управление - ИСПРАВЛЕНО: используем простые строки
        self.paused = False
        self.current_mode = 'view'  # 'view', 'water', 'extinguish'

        # Переменные ползунков
        self.prob_lightning = tk.DoubleVar(value=0.0001)
        self.prob_growth = tk.DoubleVar(value=0.01)
        self.prob_spread = tk.DoubleVar(value=0.7)
        self.prob_extinguish = tk.DoubleVar(value=0.1)

        self.setup_ui()
        self.draw_simulation()

    def setup_ui(self):
        """Настройка интерфейса"""
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Холст - ИСПРАВЛЕНО: корректная привязка клика
        canvas_width = self.grid_width * self.cell_size
        canvas_height = self.grid_height * self.cell_size

        self.canvas = tk.Canvas(
            main_frame,
            width=canvas_width,
            height=canvas_height,
            bg='#000000',
            highlightthickness=2,
            highlightbackground='#4a4a6a',
            cursor='crosshair'
        )
        self.canvas.pack(side=tk.TOP, pady=(0, 10))
        # Привязываем клик к методу с правильным обработчиком
        self.canvas.bind('<Button-1>', self.on_canvas_click)

        # Панель управления
        control_frame = tk.Frame(main_frame, bg='#16213e')
        control_frame.pack(fill=tk.X, pady=5)

        # Статистика
        stats_frame = tk.LabelFrame(control_frame, text="Статистика",
                                    bg='#16213e', fg='#e0e0e0', font=('Arial', 10, 'bold'))
        stats_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

        self.stats_labels = {}
        for key, label in [('generation', 'Поколение'), ('trees', 'Деревья'),
                           ('burning', 'Горит'), ('water', 'Вода'),
                           ('grass', 'Трава'), ('burned', 'Пепел')]:
            lbl = tk.Label(stats_frame, text=f"{label}: 0", bg='#16213e',
                           fg='#e0e0e0', font=('Arial', 9), anchor='w', width=14)
            lbl.pack(fill=tk.X, padx=5, pady=1)
            self.stats_labels[key] = lbl

        # Ползунки
        sliders_frame = tk.LabelFrame(control_frame, text="Параметры",
                                      bg='#16213e', fg='#e0e0e0', font=('Arial', 10, 'bold'))
        sliders_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

        slider_configs = [
            ('prob_lightning', 'Молния', 0.0, 0.01, 0.0001),
            ('prob_growth', 'Рост', 0.0, 0.1, 0.01),
            ('prob_spread', 'Распространение', 0.1, 1.0, 0.7),
            ('prob_extinguish', 'Тушение', 0.0, 0.5, 0.1),
        ]

        self.slider_labels = {}
        for var_name, label, min_val, max_val, initial in slider_configs:
            frame = tk.Frame(sliders_frame, bg='#16213e')
            frame.pack(fill=tk.X, padx=5, pady=2)

            tk.Label(frame, text=f"{label}:", bg='#16213e', fg='#e0e0e0',
                     font=('Arial', 9), width=13, anchor='w').pack(side=tk.LEFT)

            slider = ttk.Scale(frame, from_=min_val, to=max_val,
                               variable=getattr(self, var_name), orient=tk.HORIZONTAL, length=120)
            slider.pack(side=tk.LEFT, padx=5)

            value_lbl = tk.Label(frame, text=f"{initial:.4f}", bg='#16213e',
                                 fg='#00ff00', font=('Arial', 9, 'bold'), width=7)
            value_lbl.pack(side=tk.LEFT)

            slider.configure(command=lambda v, l=value_lbl: l.configure(text=f"{float(v):.4f}"))
            self.slider_labels[var_name] = value_lbl

        # Кнопки
        buttons_frame = tk.LabelFrame(control_frame, text="Управление",
                                      bg='#16213e', fg='#e0e0e0', font=('Arial', 10, 'bold'))
        buttons_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

        btn_config = {'bg': '#0f3460', 'fg': '#ffffff', 'font': ('Arial', 9, 'bold'),
                      'width': 12, 'height': 1, 'cursor': 'hand2'}

        self.pause_btn = tk.Button(buttons_frame, text="Пауза", command=self.toggle_pause, **btn_config)
        self.pause_btn.pack(pady=2)

        tk.Button(buttons_frame, text="Перезапуск", command=self.restart_simulation, **btn_config).pack(pady=2)

        # Режимы - ИСПРАВЛЕНО: корректное переключение
        mode_frame = tk.LabelFrame(buttons_frame, text="Режим", bg='#16213e',
                                   fg='#e0e0e0', font=('Arial', 9))
        mode_frame.pack(pady=5)

        # Используем отдельные переменные для радиокнопок
        self.mode_var = tk.StringVar(value='view')

        tk.Radiobutton(mode_frame, text="Просмотр", variable=self.mode_var, value='view',
                       bg='#16213e', fg='#e0e0e0', selectcolor='#0f3460',
                       activebackground='#16213e', activeforeground='#e0e0e0',
                       command=self.update_mode).pack(anchor='w')

        tk.Radiobutton(mode_frame, text="Добавить воду", variable=self.mode_var, value='water',
                       bg='#16213e', fg='#e0e0e0', selectcolor='#0f3460',
                       activebackground='#16213e', activeforeground='#e0e0e0',
                       command=self.update_mode).pack(anchor='w')

        tk.Radiobutton(mode_frame, text="Тушить огонь", variable=self.mode_var, value='extinguish',
                       bg='#16213e', fg='#e0e0e0', selectcolor='#0f3460',
                       activebackground='#16213e', activeforeground='#e0e0e0',
                       command=self.update_mode).pack(anchor='w')

        # Информация
        info_frame = tk.LabelFrame(control_frame, text="Инфо", bg='#16213e',
                                   fg='#e0e0e0', font=('Arial', 10, 'bold'))
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        info_text = tk.Text(info_frame, height=6, width=30, bg='#0f3460',
                            fg='#e0e0e0', font=('Arial', 8), wrap=tk.WORD, relief=tk.FLAT)
        info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        info_text.insert('1.0', """ПРАВИЛА:
1. Горящие → пепел
2. Деревья горят от соседей  
3. Молния поджигает случайно
4. Деревья растут на пустых

Выберите режим и кликните по карте""")
        info_text.configure(state='disabled')

        self.mode_label = tk.Label(main_frame, text="Режим: Просмотр",
                                   bg='#1a1a2e', fg='#00ff00', font=('Arial', 10, 'bold'))
        self.mode_label.pack(pady=5)

    def update_mode(self):
        """Обновление текущего режима - ИСПРАВЛЕНО"""
        self.current_mode = self.mode_var.get()
        mode_names = {'view': 'Просмотр', 'water': 'Добавить воду', 'extinguish': 'Тушить огонь'}
        self.mode_label.configure(text=f"Режим: {mode_names.get(self.current_mode, 'Просмотр')}")

        # Меняем курсор в зависимости от режима
        if self.current_mode == 'water':
            self.canvas.configure(cursor='boat')
        elif self.current_mode == 'extinguish':
            self.canvas.configure(cursor='target')
        else:
            self.canvas.configure(cursor='crosshair')

    def draw_simulation(self):
        """Отрисовка симуляции"""
        self.canvas.delete('all')

        for y in range(self.model.height):
            for x in range(self.model.width):
                state = self.model.grid[y, x]
                color = COLORS[state]

                if state in [TREE_YOUNG, TREE_MATURE, TREE_OLD]:
                    variation = (x + y) % 10 - 5
                    r = max(0, min(255, color[0] + variation))
                    g = max(0, min(255, color[1] + variation))
                    b = max(0, min(255, color[2] + variation))
                    color = f'#{r:02x}{g:02x}{b:02x}'
                else:
                    color = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'

                x1 = x * self.cell_size
                y1 = y * self.cell_size
                self.canvas.create_rectangle(x1, y1, x1 + self.cell_size,
                                             y1 + self.cell_size, fill=color, outline='')

    def update_stats(self):
        """Обновление статистики"""
        stats = self.model.get_stats()
        self.stats_labels['generation'].configure(text=f"Поколение: {self.model.generation}")
        self.stats_labels['trees'].configure(text=f"Деревья: {stats['trees']}")
        self.stats_labels['burning'].configure(text=f"Горит: {stats['burning']}")
        self.stats_labels['water'].configure(text=f"Вода: {stats['water']}")
        self.stats_labels['grass'].configure(text=f"Трава: {stats['grass']}")
        self.stats_labels['burned'].configure(text=f"Пепел: {stats['burned']}")

    def update_simulation(self):
        """Обновление симуляции"""
        if not self.paused:
            self.model.update(
                self.prob_lightning.get(),
                self.prob_growth.get(),
                self.prob_spread.get(),
                self.prob_extinguish.get()
            )
            self.draw_simulation()
            self.update_stats()

        self.root.after(1000 // self.fps, self.update_simulation)

    def toggle_pause(self):
        """Пауза"""
        self.paused = not self.paused
        self.pause_btn.configure(text="Продолжить" if self.paused else "Пауза")

    def restart_simulation(self):
        """Перезапуск"""
        self.model = ForestFireModel(self.grid_width, self.grid_height)
        self.model.initialize_forest()
        self.draw_simulation()
        self.update_stats()

    def on_canvas_click(self, event):
        """Обработка клика по карте - ИСПРАВЛЕНО"""
        # Корректный расчет координат клетки
        x = event.x // self.cell_size
        y = event.y // self.cell_size

        # Проверка границ
        if 0 <= x < self.model.width and 0 <= y < self.model.height:
            if self.current_mode == 'water':
                self.model.add_water(x, y, size=3)
                self.draw_simulation()
                self.update_stats()
            elif self.current_mode == 'extinguish':
                self.model.extinguish(x, y, radius=4)
                self.draw_simulation()
                self.update_stats()
            # В режиме 'view' ничего не делаем при клике

    def run(self):
        """Запуск приложения"""
        self.root.after(100, self.update_simulation)
        self.root.mainloop()


if __name__ == "__main__":

    app = ForestFireApp()
    app.run()