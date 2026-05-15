import tkinter as tk
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import csv
import threading
import time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

plt.rcParams.update({
    'figure.facecolor': '#1e1e1e',
    'axes.facecolor': '#2a2a2a',
    'axes.edgecolor': '#4a4a4a',
    'text.color': '#ffffff',
    'xtick.color': '#ffffff',
    'ytick.color': '#ffffff',
    'grid.color': '#3a3a3a',
    'grid.alpha': 0.3,
    'font.family': 'sans-serif',
    'font.size': 11
})


class WeatherContinuousMarkov(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Марковская модель погоды")
        self.geometry("1400x900")
        self.minsize(1100, 750)

        self.running = False
        self.total_time = 0.0
        self.history_time = [0.0]
        self.history_states = [1]
        self.time_spent = {1: 0.0, 2: 0.0, 3: 0.0}

        self.states = {1: "Ясно", 2: "Облачно", 3: "Пасмурно"}
        self.current_state = 1
        self.csv_file = "weather_analysis.csv"

        self.reset_csv()
        self.setup_ui()

    def reset_csv(self):
        with open(self.csv_file, 'w', newline='', encoding='utf-16') as f:
            writer = csv.writer(f)
            writer.writerow(["Total_Time", "State_ID", "Duration"])

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=16, fg_color="#262626")
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(15, 0), pady=15)
        self.sidebar.grid_rowconfigure(3, weight=1)  # Растягиваем пустое место

        ctk.CTkLabel(self.sidebar, text="Марковская модель", font=("Arial", 20, "bold")).pack(pady=(20, 10))

        matrix_card = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        matrix_card.pack(fill="x", padx=15, pady=(10, 15))

        ctk.CTkLabel(matrix_card, text="Матрица интенсивностей", font=("Arial", 15, "bold")).pack(anchor="w",
                                                                                                  pady=(0, 10))

        self.matrix_inputs = []
        labels = ["Ясно", "Облачно", "Пасмурно"]
        for i in range(3):
            ctk.CTkLabel(matrix_card, text=f"Из {labels[i]}:", font=("Arial", 13, "bold")).pack(anchor="w", padx=10,
                                                                                                pady=(8, 2))
            f = ctk.CTkFrame(matrix_card, fg_color="#1f1f1f", corner_radius=8)
            f.pack(pady=4)
            row_entries = []
            for j in range(3):
                e = ctk.CTkEntry(f, width=70, font=("Consolas", 13))
                default_val = "0.5" if i != j else "0.0"
                if i == 0 and j == 1: default_val = "0.6"
                if i == 2 and j == 1: default_val = "0.8"

                e.insert(0, default_val)
                if i == j:
                    e.configure(state="disabled", fg_color="#2c3e50", text_color="#7f8c8d")
                e.pack(side="left", padx=4, pady=4)
                row_entries.append(e)
            self.matrix_inputs.append(row_entries)

        speed_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        speed_frame.pack(fill="x", padx=20, pady=(30, 5))
        ctk.CTkLabel(speed_frame, text="Скорость симуляции:", font=("Arial", 13)).pack(anchor="w")

        self.speed_val_label = ctk.CTkLabel(speed_frame, text="1.5x", font=("Arial", 14, "bold"), text_color="#3498db")
        self.speed_val_label.pack(anchor="e", pady=(2, 0))

        self.speed_slider = ctk.CTkSlider(speed_frame, from_=0.1, to=5.0, number_of_steps=49)
        self.speed_slider.set(1.5)
        self.speed_slider.pack(fill="x", pady=(8, 5))
        self.speed_slider.configure(command=lambda v: self.speed_val_label.configure(text=f"{float(v):.1f}x"))

        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.start_btn = ctk.CTkButton(btn_frame, text="Запустить", command=self.toggle_simulation,
                                       fg_color="#2ecc71", hover_color="#27ae60", font=("Arial", 14, "bold"), height=45,
                                       corner_radius=10)
        self.start_btn.pack(fill="x")

        self.reset_btn = ctk.CTkButton(btn_frame, text="Сбросить", command=self.reset_sim,
                                       fg_color="#e74c3c", hover_color="#c0392b", font=("Arial", 14, "bold"), height=45,
                                       corner_radius=10)
        self.reset_btn.pack(fill="x", pady=(10, 0))

        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_content.grid_rowconfigure(1, weight=1)

        self.info_card = ctk.CTkFrame(self.main_content, fg_color="#262626", corner_radius=12)
        self.info_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        self.status_dot = ctk.CTkLabel(self.info_card, text="●", font=("Arial", 24), text_color="#95a5a6", width=30)
        self.status_dot.pack(side="left", padx=(20, 0), pady=20)

        self.time_label = ctk.CTkLabel(self.info_card, text="Модельное время: 0.00", font=("Arial", 22, "bold"))
        self.time_label.pack(side="left", padx=20, pady=20)

        self.state_label = ctk.CTkLabel(self.info_card, text="ОЖИДАНИЕ", font=("Arial", 32, "bold"),
                                        text_color="#bdc3c7")
        self.state_label.pack(side="right", padx=30, pady=20)

        self.fig, (self.ax_line, self.ax_bar) = plt.subplots(2, 1, figsize=(10, 8))
        self.fig.subplots_adjust(left=0.12, bottom=0.08, right=0.96, top=0.94, hspace=0.35)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_content)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

    def get_q_matrix(self):
        try:
            Q = np.zeros((3, 3))
            for i in range(3):
                row_sum = 0
                for j in range(3):
                    if i != j:
                        val = float(self.matrix_inputs[i][j].get())
                        Q[i, j] = val
                        row_sum += val
                Q[i, i] = -row_sum
            return Q
        except ValueError:
            return None

    def calculate_stationary(self, Q):
        try:
            A = Q.T
            print(A)
            A[-1] = np.ones(3)
            b = np.zeros(3)
            b[-1] = 1
            return np.linalg.solve(A, b)
        except Exception:
            return np.array([0.33, 0.33, 0.34])

    def toggle_simulation(self):
        if not self.running:
            if self.get_q_matrix() is None:
                tk.messagebox.showerror("Ошибка", "Введите корректные числа в матрицу")
                return
            self.running = True
            self.start_btn.configure(text="Остановить", fg_color="#f39c12", hover_color="#d68910")
            self.status_dot.configure(text_color="#2ecc71")
            threading.Thread(target=self.simulation_loop, daemon=True).start()
        else:
            self.running = False
            self.start_btn.configure(text="Запустить", fg_color="#2ecc71", hover_color="#27ae60")
            self.status_dot.configure(text_color="#e74c3c")

    def simulation_loop(self):
        while self.running:
            Q = self.get_q_matrix()
            theo_probs = self.calculate_stationary(Q)

            curr_i = self.current_state - 1
            lambda_out = -Q[curr_i, curr_i]

            if lambda_out > 0:
                dt = np.random.exponential(1.0 / lambda_out)
            else:
                dt = 1.0

            visual_speed = self.speed_slider.get()
            time.sleep(dt / visual_speed)

            if not self.running: break

            self.total_time += dt
            self.time_spent[self.current_state] += dt
            self.history_states.append(self.current_state)
            self.history_time.append(self.total_time)

            probabilities = []
            other_states = []
            for j in range(3):
                if curr_i != j:
                    probabilities.append(Q[curr_i, j] / lambda_out)
                    other_states.append(j + 1)

            probabilities = np.array(probabilities)
            probabilities /= probabilities.sum()

            self.update_ui_state(theo_probs)

            with open(self.csv_file, 'a', newline='', encoding='utf-16') as f:
                writer = csv.writer(f)
                writer.writerow([round(self.total_time, 3), self.current_state, round(dt, 3)])

            self.current_state = np.random.choice(other_states, p=probabilities)

    def update_ui_state(self, theo_probs):
        self.time_label.configure(text=f"Модельное время: {self.total_time:.2f}")
        self.state_label.configure(text=self.states[self.current_state], text_color="#ffffff")

        self.ax_line.clear()
        self.ax_line.step(self.history_time[-40:], self.history_states[-40:], where='post', color='#3498db',
                          linewidth=2.5)
        self.ax_line.set_yticks([1, 2, 3])
        self.ax_line.set_yticklabels(["Ясно", "Облачно", "Пасмурно"], fontsize=10)
        self.ax_line.set_ylim(0.5, 3.5)
        self.ax_line.grid(True, linestyle='--', alpha=0.4)
        self.ax_line.set_title("Траектория процесса", fontsize=13, fontweight='bold', pad=10)
        self.ax_line.tick_params(axis='x', rotation=30)

        self.ax_bar.clear()
        labels = ['Ясно', 'Облачно', 'Пасмурно']
        emp_probs = [self.time_spent[i] / self.total_time if self.total_time > 0 else 0 for i in [1, 2, 3]]

        x = np.arange(len(labels))
        width = 0.3
        rects1 = self.ax_bar.bar(x - width / 2, emp_probs, width, label='Эмп.', color='#3498db', edgecolor='#2980b9')
        rects2 = self.ax_bar.bar(x + width / 2, theo_probs, width, label='Теор.', color='#f1c40f', edgecolor='#f39c12')

        self.ax_bar.set_xticks(x)
        self.ax_bar.set_xticklabels(labels, fontsize=11)
        self.ax_bar.set_ylim(0, 1.05)
        self.ax_bar.grid(True, axis='y', linestyle='--', alpha=0.3)
        self.ax_bar.legend(facecolor='#2a2a2a', labelcolor='white', edgecolor='#4a4a4a')

        for rect in rects1:
            height = rect.get_height()
            if height > 0.01:
                self.ax_bar.text(rect.get_x() + rect.get_width() / 2., height, f'{height:.2f}',
                                 ha='center', va='bottom', color='#3498db', fontsize=9, fontweight='bold')
        for rect in rects2:
            height = rect.get_height()
            if height > 0.01:
                self.ax_bar.text(rect.get_x() + rect.get_width() / 2., height, f'{height:.2f}',
                                 ha='center', va='bottom', color='#f1c40f', fontsize=9, fontweight='bold')

        self.canvas.draw()

    def reset_sim(self):
        self.running = False
        self.total_time = 0.0
        self.current_state = 1
        self.time_spent = {1: 0.0, 2: 0.0, 3: 0.0}
        self.history_time = [0.0]
        self.history_states = [1]
        self.reset_csv()

        self.time_label.configure(text="Модельное время: 0.00")
        self.state_label.configure(text="ОЖИДАНИЕ", text_color="#bdc3c7")
        self.status_dot.configure(text_color="#95a5a6")
        self.start_btn.configure(text="Запустить", fg_color="#2ecc71", hover_color="#27ae60")

        self.ax_line.clear()
        self.ax_bar.clear()
        self.canvas.draw()


if __name__ == "__main__":
    app = WeatherContinuousMarkov()
    app.mainloop()
