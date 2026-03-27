import tkinter as tk
from tkinter import font as tkfont
import random
import time

class SimpleLCG:
    def __init__(self, seed=None):
        # Начальные данные согласно заданию
        self.state = seed if seed else int(time.time())
        self.m = 2**32
        self.a = 1664525
        self.c = 1

    def next(self):
        # Классическая формула ЛЦГ
        self.state = (self.a * self.state + self.c) % self.m
        # Приведение к интервалу [0, 1]
        return self.state / self.m

class MysticBallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Оракул Судьбы")
        self.root.geometry("450x750")
        self.root.resizable(False, False)

        self.lcg = SimpleLCG()
        self.mode = "magic"

        self.preds_yes_no = ["ДА", "НЕТ"]
        self.preds_magic = [
            "Бесспорно", "Никаких сомнений", "Вероятнее всего",
            "Пока не ясно", "Спроси позже", "НЕТ",
            "Перспективы плохие", "Весьма сомнительно"
        ]

        self.color_bg = "#0f0c29"
        self.color_acc = "#00f2fe"
        self.color_ball = "#1a1a2e"

        self.setup_fonts()
        self.create_widgets()

    def setup_fonts(self):
        try:
            self.font_title = tkfont.Font(family="Georgia", size=20, weight="bold")
            self.font_pred = tkfont.Font(family="Courier New", size=14, weight="bold")
            self.font_btn = tkfont.Font(family="Verdana", size=10, weight="bold")
        except:
            self.font_title = ("Arial", 18, "bold")
            self.font_pred = ("Consolas", 12, "bold")
            self.font_btn = ("Arial", 10, "bold")

    def create_widgets(self):
        self.canvas_bg = tk.Canvas(self.root, bg=self.color_bg, highlightthickness=0)
        self.canvas_bg.place(x=0, y=0, relwidth=1, relheight=1)
        for i in range(750):
            color = f"#{max(0, int(15 - i * 10 / 750)):02x}{max(0, int(12 - i * 8 / 750)):02x}{max(0, int(41 - i * 20 / 750)):02x}"
            self.canvas_bg.create_line(0, i, 450, i, fill=color)

        self.frame_modes = tk.Frame(self.root, bg=self.color_bg)
        self.frame_modes.pack(pady=(20, 10))

        self.btn_mode_1 = tk.Button(self.frame_modes, text="ДА/НЕТ", command=lambda: self.set_mode("binary"),
                                    relief=tk.FLAT, font=self.font_btn, width=10, bg="#1a1a3a", fg=self.color_acc)
        self.btn_mode_1.pack(side=tk.LEFT, padx=5)

        self.btn_mode_2 = tk.Button(self.frame_modes, text="MAGIC 8", command=lambda: self.set_mode("magic"),
                                    relief=tk.FLAT, font=self.font_btn, width=10, bg=self.color_acc, fg=self.color_bg)
        self.btn_mode_2.pack(side=tk.LEFT, padx=5)

        tk.Label(self.root, text="ВВЕДИТЕ ВАШ ВОПРОС:", font=("Arial", 8, "bold"), fg=self.color_acc,
                 bg=self.color_bg).pack(pady=(10, 0))
        self.question_entry = tk.Entry(self.root, font=("Arial", 12), bg="#1a1a3a", fg="white",
                                       insertbackground="white", relief=tk.FLAT, justify='center')
        self.question_entry.pack(pady=5, padx=50, fill=tk.X)

        self.ball_container = tk.Frame(self.root, width=320, height=320, bg=self.color_bg)
        self.ball_container.pack(pady=20)
        self.ball_container.pack_propagate(False)

        self.ball_canvas = tk.Canvas(self.ball_container, width=300, height=300, bg=self.color_bg, highlightthickness=0)
        self.ball_canvas.place(x=10, y=10)
        self.ball_canvas.create_oval(10, 10, 290, 290, fill=self.color_ball, outline=self.color_acc, width=2)
        self.ball_canvas.create_oval(50, 40, 120, 90, fill="#3a3a6d", outline="")

        self.pred_text = tk.Text(self.ball_canvas, width=15, height=3, font=self.font_pred,
                                 fg=self.color_ball, bg=self.color_ball, wrap=tk.WORD, relief=tk.FLAT,
                                 state=tk.DISABLED)
        self.pred_text.place(x=150, y=150, anchor=tk.CENTER)
        self.pred_text.tag_configure("center", justify='center')

        self.btn_predict = tk.Button(self.root, text="УЗНАТЬ СУДЬБУ", font=self.font_btn,
                                     command=self.shake_and_predict,
                                     bg="#242443", fg=self.color_acc, activebackground=self.color_acc, relief=tk.FLAT,
                                     pady=15, padx=30)
        self.btn_predict.pack(side=tk.BOTTOM, pady=40)

    def set_mode(self, new_mode):
        self.mode = new_mode
        if self.mode == "binary":
            self.btn_mode_1.config(fg=self.color_bg, bg=self.color_acc)
            self.btn_mode_2.config(fg=self.color_acc, bg="#1a1a3a")
        else:
            self.btn_mode_2.config(fg=self.color_bg, bg=self.color_acc)
            self.btn_mode_1.config(fg=self.color_acc, bg="#1a1a3a")

    def shake_and_predict(self):
        self.btn_predict.config(state=tk.DISABLED)
        self.pred_text.config(state=tk.NORMAL)
        self.pred_text.delete('1.0', tk.END)
        self.pred_text.config(state=tk.DISABLED, fg=self.color_ball)
        self.shake_ball(15)

    def shake_ball(self, count):
        if count > 0:
            dx, dy = random.randint(-10, 10), random.randint(-10, 10)
            self.ball_canvas.place(x=10 + dx, y=10 + dy)
            self.root.after(30, lambda: self.shake_ball(count - 1))
        else:
            self.ball_canvas.place(x=10, y=10)
            self.ball_logic()
            self.btn_predict.config(state=tk.NORMAL)

    def ball_logic(self):
        question = self.question_entry.get().lower()

        if "радмир ренатович" in question:
            answer = "БЕССУМНЕННО ДА" if self.mode == "magic" else "ДА"
        else:
            current_list = self.preds_yes_no if self.mode == "binary" else self.preds_magic
            m = len(current_list)
            pi = 1.0 / m
            alpha = self.lcg.next()
            k = int(alpha / pi)
            if k >= m: k = m - 1
            answer = current_list[k]

        self.animate_text(answer)

    def animate_text(self, text):
        self.pred_text.config(state=tk.NORMAL)
        self.pred_text.insert('1.0', text.upper())
        self.pred_text.tag_add("center", "1.0", "end")
        colors = ["#1a1a2e", "#00f2fe", "#ffffff"]
        for i, col in enumerate(colors):
            self.root.after(i * 150, lambda c=col: self.pred_text.config(fg=c))
        self.pred_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = MysticBallApp(root)
    root.mainloop()
