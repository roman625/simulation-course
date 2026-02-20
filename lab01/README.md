# Лабораторная работа №1  
## Моделирование полёта тела в атмосфере

Программа разработана на языке **Python** с использованием графического интерфейса **Tkinter**.

---

###  Исходный код программы

```python
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

class FlightSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Моделирование полёта тела в атмосфере")
        self.root.geometry("1000x750")
        self.root.configure(bg='#f0f0f0')

        # Физические константы согласно мат. модели
        self.g = 9.81      # ускорение свободного падения, м/с²
        self.rho = 1.29    # плотность воздуха, кг/м³ (согласно модели)
        self.C = 0.15      # коэффициент лобового сопротивления (баллистика)

        self.create_widgets()

    def create_widgets(self):
        # === ВЕРХНЯЯ ПАНЕЛЬ С ПАРАМЕТРАМИ ===
        params_frame = ttk.LabelFrame(self.root, text="Параметры запуска", padding=15)
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        # Высота начала
        ttk.Label(params_frame, text="Height (м):").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.height_var = tk.StringVar(value="0")
        self.height_spin = ttk.Spinbox(params_frame, from_=0, to=1000, width=10, textvariable=self.height_var)
        self.height_spin.grid(row=0, column=1, padx=5, pady=5)

        # Угол
        ttk.Label(params_frame, text="Angle (град):").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.angle_var = tk.StringVar(value="45")
        self.angle_spin = ttk.Spinbox(params_frame, from_=0, to=90, width=10, textvariable=self.angle_var)
        self.angle_spin.grid(row=1, column=1, padx=5, pady=5)

        # Скорость
        ttk.Label(params_frame, text="Speed (м/с):").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.speed_var = tk.StringVar(value="10")
        self.speed_spin = ttk.Spinbox(params_frame, from_=1, to=500, width=10, textvariable=self.speed_var)
        self.speed_spin.grid(row=2, column=1, padx=5, pady=5)

        # Шаг моделирования
        ttk.Label(params_frame, text="Step Δt (с):").grid(row=0, column=2, padx=15, pady=5, sticky='e')
        self.dt_var = tk.StringVar(value="1")
        self.dt_spin = ttk.Spinbox(params_frame, from_=0.0001, to=0.1, increment=0.01, width=10,
                                   textvariable=self.dt_var)
        self.dt_spin.grid(row=0, column=3, padx=5, pady=5)

        # Масса
        ttk.Label(params_frame, text="Mass (кг):").grid(row=1, column=2, padx=15, pady=5, sticky='e')
        self.mass_var = tk.StringVar(value="1")
        self.mass_spin = ttk.Spinbox(params_frame, from_=0.01, to=100, width=10, textvariable=self.mass_var)
        self.mass_spin.grid(row=1, column=3, padx=5, pady=5)

        # Площадь поперечного сечения
        ttk.Label(params_frame, text="Area S (м²):").grid(row=2, column=2, padx=15, pady=5, sticky='e')
        self.area_var = tk.StringVar(value="0.1")
        self.area_spin = ttk.Spinbox(params_frame, from_=0.001, to=10, increment=0.01, width=10,
                                     textvariable=self.area_var)
        self.area_spin.grid(row=2, column=3, padx=5, pady=5)

        # Кнопки
        ttk.Button(params_frame, text="Launch", command=self.launch, width=15).grid(row=3, column=0, columnspan=2,
                                                                                    padx=5, pady=10)
        ttk.Button(params_frame, text="Clear", command=self.clear_graph, width=15).grid(row=3, column=2, columnspan=2,
                                                                                        padx=5, pady=10)

        # Информация о параметрах модели
        info_frame = ttk.Frame(params_frame)
        info_frame.grid(row=0, column=4, rowspan=3, padx=20, pady=5)
        ttk.Label(info_frame, text="Параметры модели:", font=('Arial', 9, 'bold')).pack(anchor='w')
        ttk.Label(info_frame, text=f"ρ = {self.rho} кг/м³", foreground='blue').pack(anchor='w')
        ttk.Label(info_frame, text=f"C = {self.C}", foreground='blue').pack(anchor='w')
        ttk.Label(info_frame, text=f"g = {self.g} м/с²", foreground='blue').pack(anchor='w')
        ttk.Label(info_frame, text=f"k = (C·S·ρ)/(2m)", foreground='blue').pack(anchor='w')

        # === ГРАФИК ===
        graph_frame = ttk.Frame(self.root)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.figure = plt.Figure(figsize=(8, 4), dpi=100, facecolor='white')
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Траектория полёта (метод Эйлера)", fontsize=12, fontweight='bold')
        self.ax.set_xlabel("Дальность X (м)", fontsize=10)
        self.ax.set_ylabel("Высота Y (м)", fontsize=10)
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.axhline(y=0, color='k', linewidth=1)

        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # === РЕЗУЛЬТАТЫ ===
        results_frame = ttk.LabelFrame(self.root, text="Результаты моделирования", padding=10)
        results_frame.pack(fill=tk.X, padx=10, pady=10)

        self.results_tree = ttk.Treeview(results_frame, columns=("value",), show="tree", height=3)
        self.results_tree.heading("#0", text="Параметр")
        self.results_tree.column("#0", width=350)
        self.results_tree.column("value", width=150, anchor='center')

        self.results_tree.insert("", "end", text="Дальность полёта, м", values=(""), iid="range")
        self.results_tree.insert("", "end", text="Максимальная высота, м", values=(""), iid="height")
        self.results_tree.insert("", "end", text="Скорость в конечной точке, м/с", values=(""), iid="velocity")

        self.results_tree.pack(fill=tk.X)

        self.launch_count = 0
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

    def calculate_k(self, mass, area):
        """Расчёт коэффициента k по формуле: k = (C·S·ρ)/(2m)"""
        return (self.C * area * self.rho) / (2 * mass)

    def calculate_trajectory(self):
        """Расчёт траектории согласно математической модели"""
        try:
            h0 = float(self.height_var.get())
            angle = float(self.angle_var.get())
            v0 = float(self.speed_var.get())
            dt = float(self.dt_var.get())
            mass = float(self.mass_var.get())
            area = float(self.area_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте введённые данные!")
            return None

        if mass <= 0 or area <= 0 or dt <= 0:
            messagebox.showerror("Ошибка", "Параметры должны быть положительными!")
            return None

        # Вычисляем коэффициент k
        k = self.calculate_k(mass, area)

        # Начальные условия (согласно модели)
        alpha = math.radians(angle)
        vx = v0 * math.cos(alpha)  # v_x(0) = v_0·cos(α)
        vy = v0 * math.sin(alpha)  # v_y(0) = v_0·sin(α)
        x, y = 0, h0

        # Списки для хранения траектории
        x_list = [x]
        y_list = [y]
        v_list = [v0]

        # Моделирование методом Эйлера
        max_iterations = 1000000
        for i in range(max_iterations):
            # Модуль скорости: v(t) = √(v_x² + v_y²)
            v = math.sqrt(vx ** 2 + vy ** 2)

            # Согласно дифференциальным уравнениям модели:
            # dv_x/dt = -k·v_x·v
            # dv_y/dt = -g - k·v_y·v
            # Метод Эйлера:
            # v_x(t+Δt) = v_x(t) - k·v_x(t)·v(t)·Δt
            # v_y(t+Δt) = v_y(t) - (g + k·v_y(t)·v(t))·Δt

            vx_new = vx - k * vx * v * dt
            vy_new = vy - (self.g + k * vy * v) * dt

            # x(t+Δt) = x(t) + v_x(t+Δt)·Δt
            # y(t+Δt) = y(t) + v_y(t+Δt)·Δt
            x_new = x + vx_new * dt
            y_new = y + vy_new * dt

            # Обновляем значения
            vx, vy, x, y = vx_new, vy_new, x_new, y_new

            # Текущая скорость
            v_new = math.sqrt(vx ** 2 + vy ** 2)

            x_list.append(x)
            y_list.append(y)
            v_list.append(v_new)

            # Если упали на землю
            if y <= 0:
                # Интерполяция для точности
                if len(y_list) > 1 and y_list[-2] > 0:
                    ratio = y_list[-2] / (y_list[-2] - y_list[-1])
                    x_list[-1] = x_list[-2] + ratio * (x_list[-1] - x_list[-2])
                    y_list[-1] = 0
                    v_list[-1] = v_list[-2] + ratio * (v_list[-1] - v_list[-2])
                break

        return {
            'x': x_list,
            'y': y_list,
            'range': x_list[-1],
            'max_height': max(y_list),
            'final_velocity': v_list[-1]
        }

    def launch(self):
        """Запуск моделирования"""
        result = self.calculate_trajectory()

        if result is None:
            return

        color = self.colors[self.launch_count % len(self.colors)]
        dt = float(self.dt_var.get())

        # Добавляем на график
        self.ax.plot(result['x'], result['y'], color=color, linewidth=2,
                     label=f'Δt={dt:.4f} с')

        # Обновляем пределы графика
        max_x = max(result['x']) * 1.1
        max_y = max(result['y']) * 1.2
        self.ax.set_xlim(0, max(10, max_x))
        self.ax.set_ylim(0, max(3, max_y))

        self.ax.legend(loc='upper right', fontsize=8)
        self.canvas.draw()

        # Обновляем таблицу результатов
        self.results_tree.set("range", "value", f"{result['range']:.3f}")
        self.results_tree.set("height", "value", f"{result['max_height']:.3f}")
        self.results_tree.set("velocity", "value", f"{result['final_velocity']:.3f}")

        self.launch_count += 1

    def clear_graph(self):
        """Очистка графика"""
        self.ax.clear()
        self.ax.set_title("Траектория полёта (метод Эйлера)", fontsize=12, fontweight='bold')
        self.ax.set_xlabel("Дальность X (м)", fontsize=10)
        self.ax.set_ylabel("Высота Y (м)", fontsize=10)
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.axhline(y=0, color='k', linewidth=1)
        self.canvas.draw()
        self.launch_count = 0

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = FlightSimulator(root)
    root.mainloop()
```

 **Рис. 1** – код программы

---

###  Интерфейс программы

В ходе запуска программа и графики выглядят подобным образом:

 **Рис. 2** – графики и запуск кода

---

###  Результаты моделирования

В ходе отрисовки графиков была заполнена таблица с полученными данными:

| Шаг моделирования, с | 1 | 0.1 | 0.01 | 0.001 | 0.0001 |
|---------------------|---|-----|------|-------|--------|
| **Дальность полёта, м** | 6,387 | 8,731 | 9,399 | 9,465 | 9,472 |
| **Максимальная высота, м** | 0 | 2,083 | 2,412 | 2,445 | 2,448 |
| **Скорость в конечной точке, м/с** | 7,245 | 8,679 | 9,246 | 9,304 | 9,310 |

 **Табл. 1** – данные дальности полета, максимальной высоты, скорости в конечной точке

---

###  Выводы

Было интересно это запрограммировать!

Анализ данных, полученных в ходе численного моделирования, позволяет сделать следующие выводы:

1. **Сходимость результатов**: При уменьшении шага интегрирования от **1 с** до **0,0001 с** все расчётные параметры — дальность полёта, максимальная высота и скорость в конечной точке — демонстрируют устойчивую сходимость к предельным значениям. Это подтверждает корректность реализации метода Эйлера и правильность выбранной математической модели.

2. **Проблема крупного шага**: Особое внимание следует уделить результатам при шаге моделирования **Δt = 1 с**. На этом режиме расчёт даёт физически некорректные значения:
   - Максимальная высота полёта равна **нулю**, хотя тело было запущено под углом 45° с начальной скоростью 10 м/с;
   - Дальность полёта составляет 6,387 м, скорость в конечной точке — 7,245 м/с.
   
   Такие отклонения свидетельствуют о том, что шаг **Δt = 1 с** является слишком крупным для данной задачи: метод Эйлера первого порядка точности не успевает корректно отследить изменение скорости и координат, что приводит к накоплению значительной ошибки уже на первых итерациях.

3. **Оптимальный шаг**: Дальнейшее уменьшение шага до **0,001 с** обеспечивает точность лучше **1%** по всем параметрам. При шагах **0,001 с** и **0,0001 с** результаты практически стабилизируются:
   - Разница в дальности составляет всего **0,007 м** (менее 0,1%);
   - По высоте — **0,003 м**;
   - По скорости — **0,006 м/с**.
   
   Это означает, что начиная с **Δt = 0,001 с** метод достигает предельной точности, ограниченной уже не дискретизацией, а вычислительной погрешностью формата чисел с плавающей запятой.

4. **Рекомендация**: Для практических расчётов рекомендуется использовать шаг интегрирования **Δt = 0,001 с**: он обеспечивает точность свыше **99,9%** при разумных вычислительных затратах. Шаг **Δt = 1 с** следует считать неприемлемым для данной задачи, так как он приводит к качественным ошибкам в описании физической картины полёта.

