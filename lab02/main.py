import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class HeatEquationSolver:
    """Решение одномерного уравнения теплопроводности методом конечных разностей"""

    def __init__(self, L, T_left, T_right, T_initial, rho, c, lambda_):
        self.L = L
        self.T_left = T_left
        self.T_right = T_right
        self.T_initial = T_initial
        self.rho = rho
        self.c = c
        self.lambda_ = lambda_

    def solve(self, dx, dt, t_final):
        nx = int(self.L / dx) + 1
        x = np.linspace(0, self.L, nx)
        nt = int(t_final / dt)

        T = np.full(nx, self.T_initial)
        T[0] = self.T_left
        T[-1] = self.T_right

        alpha = self.lambda_ / (self.rho * self.c)
        r = alpha * dt / (dx * dx)

        center_idx = nx // 2
        center_temps = []

        for n in range(nt):
            T_new = np.copy(T)

            alpha_coef = np.zeros(nx)
            beta_coef = np.zeros(nx)

            alpha_coef[0] = 0
            beta_coef[0] = self.T_left

            for i in range(1, nx - 1):
                A = r
                B = 1 + 2 * r
                C = r
                F = T[i]

                alpha_coef[i] = C / (B - A * alpha_coef[i - 1])
                beta_coef[i] = (A * beta_coef[i - 1] + F) / (B - A * alpha_coef[i - 1])

            alpha_coef[nx - 1] = 0
            beta_coef[nx - 1] = self.T_right

            T_new[nx - 1] = self.T_right
            for i in range(nx - 2, 0, -1):
                T_new[i] = alpha_coef[i] * T_new[i + 1] + beta_coef[i]

            T_new[0] = self.T_left
            T = T_new

            if n % 10 == 0 or n == nt - 1:
                center_temps.append((n * dt, T[center_idx]))

        return x, T, center_temps


class HeatEquationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Моделирование теплопроводности в пластине")
        self.root.geometry("1200x800")

        self.create_widgets()

    def create_widgets(self):
        params_frame = ttk.LabelFrame(self.root, text="Параметры модели", padding=10)
        params_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(params_frame, text="Длина L (м):").grid(row=0, column=0, sticky=tk.W)
        self.entry_L = ttk.Entry(params_frame, width=10)
        self.entry_L.insert(0, "0.1")  # Обновлено
        self.entry_L.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(params_frame, text="T левая граница (°C):").grid(row=0, column=2, sticky=tk.W)
        self.entry_T_left = ttk.Entry(params_frame, width=10)
        self.entry_T_left.insert(0, "200.0")  # Обновлено
        self.entry_T_left.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(params_frame, text="T правая граница (°C):").grid(row=0, column=4, sticky=tk.W)
        self.entry_T_right = ttk.Entry(params_frame, width=10)
        self.entry_T_right.insert(0, "50.0")  # Обновлено
        self.entry_T_right.grid(row=0, column=5, padx=5, pady=2)

        ttk.Label(params_frame, text="T начальная (°C):").grid(row=0, column=6, sticky=tk.W)
        self.entry_T_initial = ttk.Entry(params_frame, width=10)
        self.entry_T_initial.insert(0, "20.0")  # Обновлено
        self.entry_T_initial.grid(row=0, column=7, padx=5, pady=2)

        ttk.Label(params_frame, text="Плотность ρ (кг/м³):").grid(row=1, column=0, sticky=tk.W)
        self.entry_rho = ttk.Entry(params_frame, width=10)
        self.entry_rho.insert(0, "8960.0")  # Обновлено
        self.entry_rho.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(params_frame, text="Теплоемкость c (Дж/(кг·K)):").grid(row=1, column=2, sticky=tk.W)
        self.entry_c = ttk.Entry(params_frame, width=10)
        self.entry_c.insert(0, "400.0")  # Обновлено (взято по модулю)
        self.entry_c.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(params_frame, text="λ (Вт/(м·K)):").grid(row=1, column=4, sticky=tk.W)
        self.entry_lambda = ttk.Entry(params_frame, width=10)
        self.entry_lambda.insert(0, "400.0")  # Обновлено
        self.entry_lambda.grid(row=1, column=5, padx=5, pady=2)

        ttk.Label(params_frame, text="Время (с):").grid(row=1, column=6, sticky=tk.W)
        self.entry_t_final = ttk.Entry(params_frame, width=10)
        self.entry_t_final.insert(0, "2.0")
        self.entry_t_final.grid(row=1, column=7, padx=5, pady=2)

        grid_frame = ttk.LabelFrame(self.root, text="Параметры сетки", padding=10)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(grid_frame, text="Шаг по пространству dx (м):").grid(row=0, column=0, sticky=tk.W)
        self.entry_dx = ttk.Entry(grid_frame, width=10)
        self.entry_dx.insert(0, "0.01")
        self.entry_dx.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(grid_frame, text="Шаг по времени dt (с):").grid(row=0, column=2, sticky=tk.W)
        self.entry_dt = ttk.Entry(grid_frame, width=10)
        self.entry_dt.insert(0, "0.001")
        self.entry_dt.grid(row=0, column=3, padx=5, pady=2)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.btn_solve = ttk.Button(btn_frame, text="Решить", command=self.solve_single)
        self.btn_solve.pack(side=tk.LEFT, padx=5)

        self.btn_clear = ttk.Button(btn_frame, text="Очистить", command=self.clear_results)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        graph_frame = ttk.LabelFrame(self.root, text="Распределение температуры", padding=10)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fig = Figure(figsize=(10, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        result_frame = ttk.LabelFrame(self.root, text="Результаты моделирования", padding=10)
        result_frame.pack(fill=tk.X, padx=5, pady=5)

        self.result_text = tk.Text(result_frame, height=6, width=80)
        self.result_text.pack()

    def solve_single(self):
        try:
            L = float(self.entry_L.get())
            T_left = float(self.entry_T_left.get())
            T_right = float(self.entry_T_right.get())
            T_initial = float(self.entry_T_initial.get())
            rho = float(self.entry_rho.get())
            c = float(self.entry_c.get())
            lambda_ = float(self.entry_lambda.get())
            t_final = float(self.entry_t_final.get())
            dx = float(self.entry_dx.get())
            dt = float(self.entry_dt.get())

            solver = HeatEquationSolver(L, T_left, T_right, T_initial, rho, c, lambda_)
            x, T, center_temps = solver.solve(dx, dt, t_final)

            self.ax.clear()
            self.ax.plot(x, T, 'b-', linewidth=2, label=f'dx={dx}, dt={dt}')
            self.ax.set_xlabel('x, м')
            self.ax.set_ylabel('Температура, °C')
            self.ax.set_title(f'Распределение температуры при t = {t_final} с')
            self.ax.legend()
            self.ax.grid(True)
            self.canvas.draw()

            center_idx = len(x) // 2
            T_center = T[center_idx]
            x_center = x[center_idx]

            # Расчет коэффициента температуропроводности
            alpha = lambda_ / (rho * c)

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Результаты моделирования:\n")
            self.result_text.insert(tk.END, f"Коэффициент теплопроводности λ: {lambda_} Вт/(м·K)\n")
            self.result_text.insert(tk.END, f"Коэффициент температуропроводности α: {alpha:.6f} м²/с\n")
            self.result_text.insert(tk.END, f"Количество узлов по пространству: {len(x)}\n")
            self.result_text.insert(tk.END,
                                    f"Температура в центре пластины (x = {x_center:.4f} м): {T_center:.4f} °C\n")
            self.result_text.insert(tk.END, f"Время моделирования: {t_final} с\n")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

    def clear_results(self):
        self.ax.clear()
        self.canvas.draw()
        self.result_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = HeatEquationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()