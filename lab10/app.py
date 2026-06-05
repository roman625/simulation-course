import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import simpy
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging
import math

logging.basicConfig(
    filename='simulation_log.txt',
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    filemode='w',
    encoding='utf-8'
)


class SimulationModel:
    def __init__(self, lam, mu, c, k, patience_mean, duration):
        self.lam = lam
        self.mu = mu
        self.c = c
        self.k = k
        self.patience_mean = patience_mean
        self.duration = duration

        self.env = simpy.Environment()
        self.server = simpy.Resource(self.env, capacity=c)

        self.stats = {'arrived': 0, 'served': 0, 'rejected': 0, 'reneged': 0, 'wait_times': []}
        self.queue_history = []

    def log_event(self, message):
        full_msg = f"T={self.env.now:.2f}: {message}"
        logging.info(full_msg)
        return full_msg

    def request_process(self, req_id):
        arrival_time = self.env.now
        self.stats['arrived'] += 1
        self.log_event(f"Заявка #{req_id} ПРИБЫЛА")

        if len(self.server.queue) + self.server.count >= self.k:
            self.stats['rejected'] += 1
            self.log_event(f"Заявка #{req_id} ОТКЛОНЕНА (Система полна)")
            return

        patience = random.expovariate(1.0 / self.patience_mean) if self.patience_mean > 0 else float('inf')

        with self.server.request() as req:
            results = yield req | self.env.timeout(patience)
            wait_time = self.env.now - arrival_time
            self.queue_history.append((self.env.now, len(self.server.queue)))

            if req in results:
                self.stats['wait_times'].append(wait_time)
                self.log_event(f"Заявка #{req_id} начала ОБСЛУЖИВАНИЕ (ожидание {wait_time:.2f})")

                service_time = random.expovariate(self.mu)
                yield self.env.timeout(service_time)

                self.stats['served'] += 1
                self.log_event(f"Заявка #{req_id} ЗАВЕРШЕНА")
            else:
                self.stats['reneged'] += 1
                self.log_event(f"Заявка #{req_id} ПОКИНУЛА очередь (нетерпеливость)")

    def generator(self):
        req_id = 1
        while True:
            yield self.env.timeout(random.expovariate(self.lam))
            self.env.process(self.request_process(req_id))
            req_id += 1

    def run(self, log_callback):
        self.env.process(self.generator())
        until = self.duration
        step = until / 100
        for i in range(100):
            self.env.run(until=(i + 1) * step)

        return self.stats, self.queue_history


class TheoreticalModel:
    def __init__(self, lam, mu, c, k):
        self.lam = lam
        self.mu = mu
        self.c = c
        self.k = k
        self.A = lam / mu
        self.rho = lam / (c * mu)
        self.p = self._calculate_probabilities()
        self._calculate_characteristics()

    def _calculate_probabilities(self):
        p = [0.0] * (self.k + 1)
        p[0] = 1.0
        for n in range(1, self.k + 1):
            if n <= self.c:
                p[n] = p[n-1] * self.A / n
            else:
                p[n] = p[n-1] * self.A / self.c
        sum_p = sum(p)
        if sum_p > 0:
            p = [x / sum_p for x in p]
        return p

    def _calculate_characteristics(self):
        self.P_reject = self.p[self.k]

        self.L = sum(n * self.p[n] for n in range(self.k + 1))

        self.L_s = (sum(n * self.p[n] for n in range(self.c + 1)) +
                    self.c * sum(self.p[n] for n in range(self.c + 1, self.k + 1)))

        self.L_q = sum((n - self.c) * self.p[n] for n in range(self.c + 1, self.k + 1))

        self.lam_eff = self.lam * (1 - self.P_reject)

        self.W_q = self.L_q / self.lam_eff if self.lam_eff > 0 else 0
        self.W = self.L / self.lam_eff if self.lam_eff > 0 else 0

        self.P_idle = self.p[0]
        self.P_all_busy = sum(self.p[n] for n in range(self.c, self.k + 1))

    def get_report(self):
        report = [
            ("Приведённая нагрузка A = λ/μ", f"{self.A:.4f} эрланг"),
            ("Коэффициент загрузки ρ = λ/(c·μ)", f"{self.rho:.4f} ({self.rho*100:.2f}%)"),
            ("", ""),
            ("ВЕРОЯТНОСТИ СОСТОЯНИЙ:", ""),
            ("  P(система пуста) p₀", f"{self.p[0]:.6f}"),
            ("  P(все приборы заняты)", f"{self.P_all_busy:.6f}"),
            ("  P(отказ) p_K", f"{self.P_reject:.6f} ({self.P_reject*100:.2f}%)"),
            ("", ""),
            ("СРЕДНИЕ ХАРАКТЕРИСТИКИ:", ""),
            ("  Среднее число заявок в системе L", f"{self.L:.4f}"),
            ("  Среднее число занятых приборов L_s", f"{self.L_s:.4f}"),
            ("  Средняя длина очереди L_q", f"{self.L_q:.4f}"),
            ("", ""),
            ("ВРЕМЕННЫЕ ХАРАКТЕРИКИ:", ""),
            ("  Эффективная интенсивность λ_eff", f"{self.lam_eff:.4f}"),
            ("  Среднее время ожидания W_q", f"{self.W_q:.4f}"),
            ("  Среднее время пребывания W", f"{self.W:.4f}"),
        ]
        return report


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Система M/M/c/K: Теория + Имитация")
        self.root.geometry("1400x850")
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self._setup_ui()

    def _setup_ui(self):
        ctrl_panel = ttk.LabelFrame(self.root, text=" Входные параметры ", padding=10)
        ctrl_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.inputs = {}
        params = [
            ("λ (Приход)", "5.0"), ("μ (Обслуж.)", "2.0"),
            ("c (Приборы)", "3"), ("K (Вместимость)", "10"),
            ("Терпение", "2.0"), ("Время мод.", "100")
        ]

        for i, (label, default) in enumerate(params):
            ttk.Label(ctrl_panel, text=label).grid(row=i, column=0, sticky="w", pady=5)
            ent = ttk.Entry(ctrl_panel, width=10)
            ent.insert(0, default)
            ent.grid(row=i, column=1, padx=5)
            self.inputs[label] = ent

        self.btn_run = ttk.Button(ctrl_panel, text="ПУСК", command=self.start)
        self.btn_run.grid(row=len(params), column=0, columnspan=2, pady=20, sticky="ew")

        self.log_area = scrolledtext.ScrolledText(ctrl_panel, width=30, height=20, font=("Consolas", 9))
        self.log_area.grid(row=len(params) + 1, column=0, columnspan=2)

        self.right_panel = ttk.Frame(self.root)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.top_frame = ttk.Frame(self.right_panel)
        self.top_frame.pack(fill=tk.BOTH, expand=True)

        self.fig, self.axes = plt.subplots(2, 2, figsize=(10, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.top_frame)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.theory_panel = ttk.LabelFrame(self.right_panel, text=" Теоретические характеристики (M/M/c/K без ренегатов) ", padding=10)
        self.theory_panel.pack(fill=tk.X, pady=(10, 0))

        self.theory_text = tk.Text(self.theory_panel, height=12, width=80,
                                   font=("Consolas", 10), bg="#f5f5f5", state='disabled')
        self.theory_text.pack(fill=tk.X)

    def _validate_inputs(self):
        values = {}
        warnings = []

        for label, entry in self.inputs.items():
            raw = entry.get().strip()
            if not raw:
                return False, f"Поле «{label}» не может быть пустым.", []

        float_fields = ["λ (Приход)", "μ (Обслуж.)", "Терпение", "Время мод."]
        int_fields = ["c (Приборы)", "K (Вместимость)"]

        for label in float_fields:
            raw = self.inputs[label].get().strip()
            try:
                val = float(raw)
                if math.isnan(val) or math.isinf(val):
                    return False, f"Поле «{label}» содержит недопустимое значение (inf/nan).", []
                values[label] = val
            except ValueError:
                return False, f"Поле «{label}» должно содержать число. Введено: «{raw}».", []

        for label in int_fields:
            raw = self.inputs[label].get().strip()
            try:
                f_val = float(raw)
                if f_val != int(f_val):
                    return False, f"Поле «{label}» должно быть ЦЕЛЫМ числом. Введено: «{raw}».", []
                if math.isnan(f_val) or math.isinf(f_val):
                    return False, f"Поле «{label}» содержит недопустимое значение.", []
                values[label] = int(f_val)
            except (ValueError, OverflowError):
                return False, f"Поле «{label}» должно содержать целое число. Введено: «{raw}».", []

        lam = values["λ (Приход)"]
        mu = values["μ (Обслуж.)"]
        c = values["c (Приборы)"]
        k = values["K (Вместимость)"]
        pat = values["Терпение"]
        dur = values["Время мод."]

        if lam < 0:
            return False, "Интенсивность прибытия (λ) не может быть отрицательной.", []
        if mu < 0:
            return False, "Интенсивность обслуживания (μ) не может быть отрицательной.", []
        if pat < 0:
            return False, "Время терпения не может быть отрицательным.", []
        if dur < 0:
            return False, "Время моделирования не может быть отрицательным.", []

        if lam == 0:
            return False, "Интенсивность прибытия (λ) должна быть > 0.", []
        if mu == 0:
            return False, "Интенсивность обслуживания (μ) должна быть > 0.", []
        if dur == 0:
            return False, "Время моделирования должно быть > 0.", []

        if c <= 0:
            return False, "Число приборов (c) должно быть ≥ 1.", []
        if k <= 0:
            return False, "Вместимость системы (K) должна быть ≥ 1.", []

        if k < c:
            return False, (f"Вместимость системы (K={k}) не может быть меньше "
                           f"числа приборов (c={c}). Должно быть K ≥ c."), []

        MAX_LAM, MAX_MU, MAX_C, MAX_K, MAX_DURATION = 10000, 10000, 1000, 100000, 1000000

        if lam > MAX_LAM:
            return False, f"Интенсивность λ={lam} слишком велика (макс. {MAX_LAM}).", []
        if mu > MAX_MU:
            return False, f"Интенсивность μ={mu} слишком велика (макс. {MAX_MU}).", []
        if c > MAX_C:
            return False, f"Число приборов c={c} слишком велико (макс. {MAX_C}).", []
        if k > MAX_K:
            return False, f"Вместимость K={k} слишком велика (макс. {MAX_K}).", []
        if dur > MAX_DURATION:
            return False, f"Время моделирования слишком велико (макс. {MAX_DURATION}).", []

        if lam < 1e-6:
            return False, "Интенсивность λ слишком мала.", []
        if mu < 1e-6:
            return False, "Интенсивность μ слишком мала.", []
        if dur < 1:
            return False, "Время моделирования слишком мало (минимум 1).", []

        rho = lam / (c * mu)
        if rho > 2.0:
            warnings.append(f"Система сильно перегружена (ρ = {rho:.2f} >> 1).")
        if rho < 0.05:
            warnings.append(f"Система почти простаивает (ρ = {rho:.3f} << 1).")
        if dur < 100:
            warnings.append(f"Время моделирования ({dur}) мало. Рекомендуется ≥ 1000.")
        if pat > 1000:
            warnings.append(f"Время терпения ({pat}) очень велико.")
        if k > 10000:
            warnings.append(f"Вместимость K={k} очень велика.")

        return True, {
            'lam': lam, 'mu': mu, 'c': c, 'k': k, 'pat': pat, 'dur': dur
        }, warnings

    def start(self):
        success, result, warnings = self._validate_inputs()

        if not success:
            messagebox.showerror("Ошибка ввода", result)
            return

        if warnings:
            warning_text = "\n\n".join(warnings) + "\n\nПродолжить моделирование?"
            if not messagebox.askyesno("Предупреждения", warning_text):
                return

        try:
            self.btn_run.config(state='disabled')
            self.log_area.delete(1.0, tk.END)
            self.log_area.insert(tk.END, "Запуск моделирования...\n")
            self.root.update()

            data = result

            theory = TheoreticalModel(data['lam'], data['mu'], data['c'], data['k'])
            self._show_theory(theory)

            model = SimulationModel(data['lam'], data['mu'], data['c'],
                                    data['k'], data['pat'], data['dur'])

            stats, history = model.run(lambda msg: self.log_area.insert(tk.END, msg))
            self._update_plots(stats, history, theory)

            total = stats['arrived']
            res_msg = (
                f"\n{'=' * 30}\n"
                f"ИТОГО (ИМИТАЦИЯ):\n"
                f"{'=' * 30}\n"
                f"Прибыло заявок:    {total}\n"
                f"Обслужено:         {stats['served']} "
                f"({stats['served'] / total * 100:.1f}%)\n" if total > 0 else "Обслужено: 0\n"
                f"Отказов:           {stats['rejected']} "
                f"({stats['rejected'] / total * 100:.1f}%)\n" if total > 0 else "Отказов: 0\n"
                f"Ушли из очереди:   {stats['reneged']} "
                f"({stats['reneged'] / total * 100:.1f}%)\n" if total > 0 else "Ушли: 0\n"
            )
            if stats['wait_times']:
                avg_wait = sum(stats['wait_times']) / len(stats['wait_times'])
                res_msg += f"Среднее ожидание:    {avg_wait:.4f}\n"

            self.log_area.insert(tk.END, res_msg)
            self.log_area.see(tk.END)

            messagebox.showinfo("Готово",
                                "Моделирование завершено.\nПодробный лог в simulation_log.txt")

        except Exception as e:
            messagebox.showerror("Ошибка выполнения", f"Произошла ошибка во время моделирования:\n{e}")
        finally:
            self.btn_run.config(state='normal')

    def _show_theory(self, theory):
        self.theory_text.config(state='normal')
        self.theory_text.delete(1.0, tk.END)

        report = theory.get_report()
        for label, value in report:
            if label == "" and value == "":
                self.theory_text.insert(tk.END, "\n")
            elif value == "":
                self.theory_text.insert(tk.END, f"{label}\n")
            else:
                self.theory_text.insert(tk.END, f"{label:<40} {value}\n")

        self.theory_text.config(state='disabled')

    def _update_plots(self, stats, history, theory):
        for ax in self.axes.flat:
            ax.clear()

        labels = ['Обслужено', 'Отказ', 'Ушли']
        values = [stats['served'], stats['rejected'], stats['reneged']]

        if sum(values) == 0:
            self.axes[0, 0].text(0.5, 0.5, 'Нет данных',
                                 ha='center', va='center', fontsize=12)
        else:
            self.axes[0, 0].pie(values, labels=labels, autopct='%1.1f%%',
                                colors=['#71e096', '#ff6b6b', '#ffd93d'], startangle=140)
        self.axes[0, 0].set_title("Имитация: исходы заявок")

        if history:
            t, q = zip(*history)
            self.axes[0, 1].step(t, q, where='post', color='#4dabf7', linewidth=1.5)
            self.axes[0, 1].fill_between(t, q, step="post", alpha=0.2, color='#4dabf7')
            self.axes[0, 1].axhline(y=theory.L_q, color='r', linestyle='--',
                                    label=f'Теория L_q={theory.L_q:.2f}')
            self.axes[0, 1].set_title("Динамика очереди (красная — теория)")
            self.axes[0, 1].set_xlabel("Время")
            self.axes[0, 1].set_ylabel("Кол-во в очереди")
            self.axes[0, 1].legend()
        else:
            self.axes[0, 1].text(0.5, 0.5, 'Нет данных',
                                 ha='center', va='center', fontsize=12)

        n_vals = list(range(theory.k + 1))
        self.axes[1, 0].bar(n_vals, theory.p, color='#9c88ff', edgecolor='black')
        self.axes[1, 0].axvline(x=theory.c, color='r', linestyle='--',
                                label=f'c={theory.c} (граница очереди)')
        self.axes[1, 0].set_title("Теория: вероятности состояний pₙ")
        self.axes[1, 0].set_xlabel("Число заявок в системе n")
        self.axes[1, 0].set_ylabel("Вероятность pₙ")
        self.axes[1, 0].legend()

        sim_p_reject = stats['rejected'] / stats['arrived'] if stats['arrived'] > 0 else 0
        sim_p_renege = stats['reneged'] / stats['arrived'] if stats['arrived'] > 0 else 0
        sim_p_served = stats['served'] / stats['arrived'] if stats['arrived'] > 0 else 0

        theory_p_served = 1 - theory.P_reject

        comparison_labels = ['P(обслуж.)', 'P(отказ)']
        theory_vals = [theory_p_served, theory.P_reject]
        sim_vals = [sim_p_served, sim_p_reject]

        x = range(len(comparison_labels))
        width = 0.35
        self.axes[1, 1].bar([i - width/2 for i in x], theory_vals, width,
                            label='Теория (M/M/c/K)', color='#54a0ff')
        self.axes[1, 1].bar([i + width/2 for i in x], sim_vals, width,
                            label='Имитация (с ренегатами)', color='#ff6b6b')
        self.axes[1, 1].set_xticks(list(x))
        self.axes[1, 1].set_xticklabels(comparison_labels)
        self.axes[1, 1].set_ylabel('Вероятность')
        self.axes[1, 1].set_title('Теория vs Имитация\n(разница — эффект нетерпеливости)')
        self.axes[1, 1].legend()

        self.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
