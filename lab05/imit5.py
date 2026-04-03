import tkinter as tk
from tkinter import ttk
import random
import math

class RouletteWithOracle:
    def __init__(self, root):
        self.root = root
        self.root.title("Рулетка")
        self.root.geometry("1100x850")
        self.root.configure(bg="#0a2e1f")

        self.balance = 1000
        self.current_bet = None
        self.spinning = False
        self.angle = 0

        self.reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        self.wheel_order = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20,
                            14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

        style = ttk.Style()
        style.configure("TNotebook", background="#051a12")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.tab_game = tk.Frame(self.notebook, bg="#0a2e1f")
        self.tab_yesno = tk.Frame(self.notebook, bg="#1a1a1a")

        self.notebook.add(self.tab_game, text=" ИГРАТЬ ")
        self.notebook.add(self.tab_yesno, text=" ДА / НЕТ ")

        self.setup_game_ui()
        self.setup_yesno_ui()

    def get_yes_no(self, p=0.5):
        return "ДА" if random.random() < p else "НЕТ"

    def setup_game_ui(self):
        self.lbl_balance = tk.Label(self.tab_game, text=f"БАЛАНС: ${self.balance}", font=("Arial", 20, "bold"),
                                    fg="#f1c40f", bg="#0a2e1f")
        self.lbl_balance.pack(pady=10)

        main_area = tk.Frame(self.tab_game, bg="#0a2e1f")
        main_area.pack(expand=True, fill=tk.BOTH)

        self.canvas = tk.Canvas(main_area, width=450, height=450, bg="#0a2e1f", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=30)

        self.table_frame = tk.Frame(main_area, bg="#1a4731", padx=10, pady=10, relief=tk.RAISED, border=3)
        self.table_frame.pack(side=tk.RIGHT, padx=30)
        self.create_betting_table()

        self.lbl_status = tk.Label(self.tab_game, text="СДЕЛАЙТЕ СТАВКУ", font=("Arial", 16, "bold"), bg="#0a2e1f",
                                   fg="white")
        self.lbl_status.pack(pady=10)

        ctrls = tk.Frame(self.tab_game, bg="#051a12", pady=15)
        ctrls.pack(fill=tk.X)

        self.chip_var = tk.IntVar(value=10)
        for v in [10, 50, 100, 500]:
            tk.Radiobutton(ctrls, text=f"${v}", variable=self.chip_var, value=v, indicatoron=False, width=6).pack(
                side=tk.LEFT, padx=5)

        self.btn_spin = tk.Button(ctrls, text="КРУТИТЬ", font=("Arial", 14, "bold"), bg="#f1c40f", width=15,
                                  command=self.start_spin)
        self.btn_spin.pack(side=tk.RIGHT, padx=20)

        self.draw_wheel(0)

    def create_betting_table(self):
        nums = [[3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
                [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
                [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]]

        tk.Button(self.table_frame, text="0", bg="green", fg="white", width=4, height=6,
                  command=lambda: self.set_bet("num", 0)).grid(row=0, column=0, rowspan=3, sticky="nswe")
        for r in range(3):
            for c in range(12):
                n = nums[r][c]
                clr = "#e74c3c" if n in self.reds else "#2c3e50"
                tk.Button(self.table_frame, text=str(n), bg=clr, fg="white", width=4, height=2,
                          command=lambda num=n: self.set_bet("num", num)).grid(row=r, column=c + 1)

        tk.Button(self.table_frame, text="RED", bg="#e74c3c", fg="white", height=2,
                  command=lambda: self.set_bet("color", "red")).grid(row=3, column=1, columnspan=6, sticky="we")
        tk.Button(self.table_frame, text="BLACK", bg="#2c3e50", fg="white", height=2,
                  command=lambda: self.set_bet("color", "black")).grid(row=3, column=7, columnspan=6, sticky="we")

    def set_bet(self, t, v):
        if self.spinning: return
        self.current_bet = (t, v)
        self.lbl_status.config(text=f"Ставка на {v} (${self.chip_var.get()})", fg="#f1c40f")

    def draw_wheel(self, angle_offset):
        self.canvas.delete("w")
        cx, cy, r = 225, 225, 190
        step = 360 / 37
        for i, num in enumerate(self.wheel_order):
            start = (i * step) - angle_offset - 90 - (step / 2)
            clr = "green" if num == 0 else ("#e74c3c" if num in self.reds else "#2c3e50")
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=-start, extent=-step, fill=clr,
                                   outline="white", tags="w")
            rad = math.radians(start + step / 2)
            self.canvas.create_text(cx + (r - 25) * math.cos(rad), cy + (r - 25) * math.sin(rad), text=str(num),
                                    fill="white", font=("Arial", 8, "bold"), tags="w")
        self.canvas.create_polygon(cx - 12, 0, cx + 12, 0, cx, 35, fill="yellow", outline="black")

    #  ИСПРАВЛЕННЫЙ МЕТОД ВЫБОРА ЧИСЛА 
    def start_spin(self):
        if self.spinning or not self.current_bet: return
        amt = self.chip_var.get()
        if self.balance < amt: return

        self.balance -= amt
        self.lbl_balance.config(text=f"БАЛАНС: ${self.balance}")
        self.spinning = True
        self.btn_spin.config(state=tk.DISABLED)
        self.angle = 0

        # ПРИНЦИП КУМУЛЯТИВНОЙ ВЕРОЯТНОСТИ
        m = len(self.wheel_order)
        p_i = 1.0 / m                
        alpha = random.random()      
        cumulative_p = 0.0
        win_num = self.wheel_order[-1] 

        for k in range(m):
            cumulative_p += p_i
            if alpha < cumulative_p:
                win_num = self.wheel_order[k]
                break

        win_idx = self.wheel_order.index(win_num)
        target_stop = win_idx * (360 / 37)
        total_dist = (360 * 5) + target_stop

        self.animate(0, total_dist, win_num)

    def animate(self, curr, total, win_num):
        if curr < total:
            step = max(0.5, (total - curr) / 20)
            self.angle = (self.angle + step) % 360
            self.draw_wheel(self.angle)
            self.root.after(20, lambda: self.animate(curr + step, total, win_num))
        else:
            self.spinning = False
            self.btn_spin.config(state=tk.NORMAL)
            self.check_result(win_num)

    def check_result(self, win_num):
        b_type, b_val = self.current_bet
        win_clr = "green" if win_num == 0 else ("red" if win_num in self.reds else "black")

        payout = 0
        if b_type == "num" and b_val == win_num:
            payout = self.chip_var.get() * 36
        elif b_type == "color" and b_val == win_clr:
            payout = self.chip_var.get() * 2

        if payout > 0:
            self.balance += payout
            self.lbl_status.config(text=f"ВЫИГРЫШ! Выпало {win_num}. +${payout}", fg="#2ecc71")
        else:
            self.lbl_status.config(text=f"ПРОИГРЫШ! Выпало {win_num}", fg="#e74c3c")
        self.lbl_balance.config(text=f"БАЛАНС: ${self.balance}")
        self.current_bet = None

    def setup_yesno_ui(self):
        tk.Label(self.tab_yesno, text="МАГИЧЕСКИЙ ОРАКУЛ", font=("Arial", 26, "bold"), fg="#9b59b6", bg="#1a1a1a").pack(
            pady=60)
        self.lbl_yesno_res = tk.Label(self.tab_yesno, text="???", font=("Arial", 60, "bold"), fg="white", bg="#1a1a1a")
        self.lbl_yesno_res.pack(pady=40)
        tk.Button(self.tab_yesno, text="УЗНАТЬ СУДЬБУ", font=("Arial", 16, "bold"), bg="#8e44ad", fg="white",
                  width=20, height=2, command=self.update_yesno).pack(pady=20)

    def update_yesno(self):
        result = self.get_yes_no()
        color = "#2ecc71" if result == "ДА" else "#e74c3c"
        self.lbl_yesno_res.config(text=result, fg=color)

if __name__ == "__main__":
    root = tk.Tk()
    app = RouletteWithOracle(root)
    root.mainloop()
