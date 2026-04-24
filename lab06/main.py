import numpy as np
import random
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.stats import chi2, norm
import tkinter as tk
from tkinter import ttk, messagebox

CLR_BG = "#2c3e50"
CLR_SIDE = "#34495e"
CLR_BASE = "#ecf0f1"
CLR_ACT = "#2980b9"
CLR_ACC = "#3498db"
CLR_W = "#ffffff"
CLR_B = "#2c3e50"

class LabAnalyzerApp:
    def __init__(self, window):
        self.window = window
        self.window.title("6 лаба")
        self.window.geometry("1200x800")
        self.window.configure(bg=CLR_BG)

        self.apply_styles()
        self.init_ui()

    def init_ui(self):
        self.root_layout = tk.Frame(self.window, bg=CLR_BG)
        self.root_layout.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.left_panel = tk.Frame(self.root_layout, bg=CLR_SIDE, width=280, bd=2, relief="groove")
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        self.left_panel.pack_propagate(False)

        tk.Label(self.left_panel, text="ПАРАМЕТРЫ", bg=CLR_SIDE, fg=CLR_W, font=("Verdana", 11, "bold")).pack(pady=(20, 10))

        self.engine_mode = tk.StringVar(value="DISCRETE")
        mode_box = tk.Frame(self.left_panel, bg=CLR_SIDE)
        mode_box.pack(fill=tk.X, padx=15, pady=5)

        self.btn_mode_d = tk.Button(mode_box, text="Дискретная", command=self.switch_to_dsv, font=("Tahoma", 9), cursor="hand2", bg=CLR_BASE)
        self.btn_mode_d.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.btn_mode_n = tk.Button(mode_box, text="Нормальная", command=self.switch_to_norm, font=("Tahoma", 9), cursor="hand2", bg=CLR_BASE)
        self.btn_mode_n.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        self.input_area = tk.Frame(self.left_panel, bg=CLR_SIDE)
        self.input_area.pack(fill=tk.BOTH, expand=True, pady=10, padx=15)

        self.input_rows = []

        ctrl_frame = tk.Frame(self.left_panel, bg=CLR_SIDE)
        ctrl_frame.pack(fill=tk.X, padx=15, pady=20)
        tk.Label(ctrl_frame, text="Выборка (N):", bg=CLR_SIDE, fg=CLR_W).pack(anchor=tk.W)
        self.field_n = tk.Entry(ctrl_frame, font=("Arial", 10)); self.field_n.insert(0, "5000"); self.field_n.pack(fill=tk.X, pady=5)

        self.run_trigger = tk.Button(self.left_panel, text="РАССЧИТАТЬ", command=self.start_process, bg=CLR_ACT, fg="white", font=("Verdana", 10, "bold"), cursor="hand2")
        self.run_trigger.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=20, ipady=8)

        self.right_zone = tk.Frame(self.root_layout, bg=CLR_BG)
        self.right_zone.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.visual_frame = tk.Frame(self.right_zone, bg="white", bd=1, relief="solid")
        self.visual_frame.pack(fill=tk.BOTH, expand=True)

        self.plot_fig, self.plot_ax = plt.subplots(figsize=(5, 3.5)); self.plot_fig.patch.set_facecolor("#f9f9f9")
        self.plot_canvas = FigureCanvasTkAgg(self.plot_fig, master=self.visual_frame); self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.info_hub = tk.Frame(self.right_zone, bg=CLR_BG)
        self.info_hub.pack(fill=tk.X, pady=(15, 0))
        self.card_m = self.build_indicator(self.info_hub, "Мат. ожидание")
        self.card_d = self.build_indicator(self.info_hub, "Дисперсия")
        self.card_x = self.build_indicator(self.info_hub, "Хи-квадрат")

        self.table_zone = tk.Frame(self.right_zone, bg=CLR_BASE)
        self.table_zone.pack(fill=tk.X, pady=(15, 0))
        self.init_table()
        self.switch_to_dsv()

    def apply_styles(self):
        s = ttk.Style(); s.theme_use('default')
        s.configure("Treeview", rowheight=25, font=("Arial", 9))
        s.configure("Treeview.Heading", font=("Arial", 8, "bold"), background="#bdc3c7")

    def build_indicator(self, parent, title):
        f = tk.Frame(parent, bg=CLR_BASE, bd=1, relief="ridge"); f.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
        tk.Label(f, text=title, bg=CLR_BASE, font=("Arial", 8, "italic")).pack(pady=(5, 0))
        v = tk.Label(f, text="---", bg=CLR_BASE, font=("Courier", 10, "bold"), fg=CLR_B); v.pack(pady=10)
        return v

    def init_table(self):
        top_bar = tk.Frame(self.table_zone, bg="#dcdde1"); top_bar.pack(fill=tk.X)
        tk.Label(top_bar, text=" Лог испытаний", bg="#dcdde1", font=("Arial", 9, "bold")).pack(side=tk.LEFT, pady=5)
        tk.Button(top_bar, text="Прогнать серию N", command=self.auto_test, font=("Arial", 8), bg="#bdc3c7").pack(side=tk.RIGHT, padx=5)
        cols = ("n_val", "m_emp", "m_err", "d_emp", "d_err", "chi_e", "chi_k", "status")
        self.data_grid = ttk.Treeview(self.table_zone, columns=cols, show="headings", height=5)
        heads = ["N", "E эмп", "Погр E", "D эмп", "Погр D", "χ² эмп", "χ² крит", "Результат"]
        for c, h in zip(cols, heads):
            self.data_grid.heading(c, text=h); self.data_grid.column(c, width=105, anchor=tk.CENTER)
        self.data_grid.pack(fill=tk.BOTH, expand=True)

    def switch_to_dsv(self):
        self.engine_mode.set("DISCRETE")
        self.btn_mode_d.config(bg=CLR_ACC, fg="white"); self.btn_mode_n.config(bg=CLR_BASE, fg="black")
        for w in self.input_area.winfo_children(): w.destroy()
        self.input_rows = []
        container = tk.Frame(self.input_area, bg=CLR_SIDE); container.pack(fill=tk.X)
        for i, p in enumerate([0.2, 0.5, 0.3]): self.add_row_dsv(container, i + 1, p)
        tk.Button(self.input_area, text="+ Добавить вариант", command=lambda: self.add_row_dsv(container, len(self.input_rows)+1, 0), bg="#95a5a6", font=("Arial", 8)).pack(pady=10)

    def add_row_dsv(self, master, x, p):
        r = tk.Frame(master, bg=CLR_SIDE); r.pack(fill=tk.X, pady=2)
        tk.Label(r, text="X:", bg=CLR_SIDE, fg="white").pack(side=tk.LEFT)
        ex = tk.Entry(r, width=4); ex.insert(0, str(x)); ex.pack(side=tk.LEFT, padx=2)
        tk.Label(r, text="P:", bg=CLR_SIDE, fg="white").pack(side=tk.LEFT)
        ep = tk.Entry(r, width=6); ep.insert(0, str(p)); ep.pack(side=tk.LEFT, padx=2)
        self.input_rows.append((ex, ep))

    def switch_to_norm(self):
        self.engine_mode.set("NORMAL")
        self.btn_mode_n.config(bg=CLR_ACC, fg="white"); self.btn_mode_d.config(bg=CLR_BASE, fg="black")
        for w in self.input_area.winfo_children(): w.destroy()
        tk.Label(self.input_area, text="Среднее (μ):", bg=CLR_SIDE, fg="white").pack(anchor=tk.W, pady=(10,0))
        self.f_mu = tk.Entry(self.input_area); self.f_mu.insert(0, "0"); self.f_mu.pack(fill=tk.X)
        tk.Label(self.input_area, text="Отклонение (σ):", bg=CLR_SIDE, fg="white").pack(anchor=tk.W, pady=(10,0))
        self.f_sigma = tk.Entry(self.input_area); self.f_sigma.insert(0, "1.0"); self.f_sigma.pack(fill=tk.X)

    def dsv_generator(self, xs, ps, N):
        res = []
        cum_ps = np.cumsum(ps)
        for _ in range(N):
            r = random.random()
            for i, c in enumerate(cum_ps):
                if r <= c:
                    res.append(xs[i])
                    break
        return np.array(res)

    def box_muller_norm(self, mu, sigma, N):
        res = []
        for _ in range(N):
            u1, u2 = random.random(), random.random()
            z0 = math.sqrt(-2.0 * math.log(u1 + 1e-9)) * math.cos(2.0 * math.pi * u2)
            res.append(mu + z0 * sigma)
        return np.array(res)

    def start_process(self):
        try: self.compute_logic(int(self.field_n.get()))
        except: messagebox.showwarning("Ошибка", "Данные некорректны")

    def auto_test(self):
        for row in self.data_grid.get_children(): self.data_grid.delete(row)
        for n in [10, 100, 1000, 10000]:
            stats = self.compute_logic(n, ui=False)
            res_text = "Принята" if stats['res'] == "OK" else "Отвергнута"
            self.data_grid.insert("", tk.END, values=(n, f"{stats['em']:.2f}", f"{stats['errem']:.1%}", f"{stats['ev']:.2f}", f"{stats['errev']:.1%}", f"{stats['chi_e']:.2f}", f"{stats['chi_k']:.2f}", res_text))

    def compute_logic(self, N, ui=True):
        if self.engine_mode.get() == "DISCRETE":
            xs = np.array([float(r[0].get()) for r in self.input_rows])
            ps = np.array([float(r[1].get()) for r in self.input_rows]); ps /= ps.sum()
            t_m = np.sum(xs * ps)
            t_v = np.sum(xs**2 * ps) - t_m**2
            sample = self.dsv_generator(xs, ps, N)
            e_m, e_v = np.mean(sample), np.var(sample)
            err_m = abs(e_m - t_m) / abs(t_m) if t_m != 0 else abs(e_m)
            err_v = abs(e_v - t_v) / abs(t_v) if t_v != 0 else abs(e_v)
            counts = np.array([np.sum(sample == x) for x in xs])
            chi_e = np.sum(((counts - N*ps)**2) / (N*ps + 1e-9))
            chi_k = chi2.ppf(0.95, len(xs)-1)
            res = "OK" if chi_e < chi_k else "FAIL"
            if ui:
                self.plot_ax.clear(); self.plot_ax.hist(sample, bins=len(xs)*2, color=CLR_ACC, alpha=0.7)
                self.plot_ax.set_title("Частоты ДСВ"); self.plot_canvas.draw()
                self.card_m.config(text=f"Т:{t_m:.2f}\nЭ:{e_m:.2f}"); self.card_d.config(text=f"Т:{t_v:.2f}\nЭ:{e_v:.2f}"); self.card_x.config(text=f"Э:{chi_e:.1f}\nК:{chi_k:.1f}")
            return {'em': e_m, 'errem': err_m, 'ev': e_v, 'errev': err_v, 'chi_e': chi_e, 'chi_k': chi_k, 'res': res}
        else:
            mu, sig = float(self.f_mu.get()), float(self.f_sigma.get())
            sample = self.box_muller_norm(mu, sig, N)
            e_m, e_v = np.mean(sample), np.var(sample)
            t_v = sig**2
            k = int(1 + math.log2(N))
            cnts, bns = np.histogram(sample, bins=k)
            p_exp = np.diff(norm.cdf(bns, mu, sig))
            chi_e = np.sum(((cnts - N*p_exp)**2) / (N*p_exp + 1e-9))
            chi_k = chi2.ppf(0.95, k-1)
            res = "OK" if chi_e < chi_k else "FAIL"
            if ui:
                self.plot_ax.clear(); self.plot_ax.hist(sample, bins=k, density=True, color="#2ecc71", alpha=0.5)
                self.plot_ax.set_title("Плотность НепрСВ"); self.plot_canvas.draw()
                self.card_m.config(text=f"Т:{mu:.2f}\nЭ:{e_m:.2f}"); self.card_d.config(text=f"Т:{t_v:.2f}\nЭ:{e_v:.2f}"); self.card_x.config(text=f"Э:{chi_e:.1f}\nК:{chi_k:.1f}")
            return {'em': e_m, 'errem': abs(e_m-mu), 'ev': e_v, 'errev': abs(e_v-t_v)/t_v, 'chi_e': chi_e, 'chi_k': chi_k, 'res': res}

if __name__ == "__main__":
    root = tk.Tk(); app = LabAnalyzerApp(root); root.mainloop()