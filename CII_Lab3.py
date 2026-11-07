import tkinter as tk
from tkinter import ttk, messagebox

class IrrigationSystem:
    def __init__(self, filename):
        self.vars = {}
        self.terms = {}
        self.rules = []
        self.parse_file(filename)

    def parse_file(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                
                parts = line.split()
                if parts[0] == 'VAR':
                    self.vars[parts[1]] = (float(parts[2]), float(parts[3]))
                    self.terms[parts[1]] = {}
                elif parts[0] == 'TERM':
                    var, term, a, b, c = parts[1], parts[2], float(parts[3]), float(parts[4]), float(parts[5])
                    self.terms[var][term] = (a, b, c)
                elif parts[0] == 'RULE':
                    conds_str = line.split(' IF ')[1].split(' THEN ')
                    conditions = []
                    for cond in conds_str[0].split(' AND '):
                        v, t = cond.split('=')
                        conditions.append((v.strip(), t.strip()))
                    
                    out_var, out_term = conds_str[1].split('=')
                    self.rules.append({
                        'conds': conditions,
                        'out_var': out_var.strip(),
                        'out_term': out_term.strip()
                    })

    def membership(self, x, a, b, c):
        if x <= a or x >= c: return 0.0
        if x == b: return 1.0
        if x < b: return (x - a) / (b - a)
        return (c - x) / (c - b)

    def get_universe(self, var, step=5):
        mn, mx = self.vars[var]
        return [mn + i * step for i in range(int((mx - mn) / step) + 1)]

    def get_set(self, var, term, universe):
        a, b, c = self.terms[var][term]
        return [self.membership(x, a, b, c) for x in universe]

    def to_singleton(self, var, value, universe):
        return [1.0 if abs(x - value) < 0.1 else 0.0 for x in universe]

    def algorithm_1(self, input_var, input_val, out_var, imp_type, agg_type, log_func):
        x_univ = self.get_universe(input_var, step=1)
        y_univ = self.get_universe(out_var, step=5)
        A_prime = self.to_singleton(input_var, input_val, x_univ)
        B_agg = [0.0] * len(y_univ)

        log_func(f"1. ФАЗИФИКАЦИЯ (перевод числа в нечеткость)")
        log_func(f"   Пользователь задал {input_var} = {input_val}. Система разбивает диапазон на шаги: от {x_univ[0]} до {x_univ[-1]}.")
        log_func("")
        log_func(f"2. ЛОГИЧЕСКИЙ ВЫВОД")
        log_func(f"   Метод: импликация {imp_type.upper()}, агрегация {agg_type.upper()}.")
        
        rule_count = 0
        for rule in self.rules:
            if rule['conds'][0][0] != input_var: continue
            rule_count += 1
            
            term_in = rule['conds'][0][1]
            A = self.get_set(input_var, term_in, x_univ)
            B = self.get_set(out_var, rule['out_term'], y_univ)
            
            R = []
            for i in range(len(x_univ)):
                row = []
                for j in range(len(y_univ)):
                    if imp_type == 'mamdani': row.append(min(A[i], B[j]))
                    else: row.append(A[i] * B[j])
                R.append(row)
            
            B_rule = []
            for j in range(len(y_univ)):
                col_max = 0.0
                for i in range(len(x_univ)):
                    if A_prime[i] > 0:
                        col_max = max(col_max, min(A_prime[i], R[i][j]))
                B_rule.append(col_max)
            
            log_func(f"   Правило {rule_count}: ЕСЛИ {input_var} = {term_in}, ТО {out_var} = {rule['out_term']}")
            log_func(f"      Степень принадлежности входа к терму '{term_in}': {A[int(input_val)]:.2f}")
            log_func(f"      Максимальная степень после композиции: {max(B_rule):.2f}")
            
            for j in range(len(y_univ)):
                if agg_type == 'max': B_agg[j] = max(B_agg[j], B_rule[j])
                else: B_agg[j] = min(1.0, B_agg[j] + B_rule[j])
        
        log_func("")
        log_func("3. АГРЕГАЦИЯ (объединение результатов всех правил)")
        if agg_type == 'max':
            log_func("   Оператор агрегации: max (берем максимум по каждому значению выхода).")
            log_func("   Формула: B'(y) = max(B_1(y), B_2(y), ..., B_n(y))")
        else:
            log_func("   Оператор агрегации: sum (алгебраическая сумма).")
            log_func("   Формула: B'(y) = min(1, B_1(y) + B_2(y) + ... + B_n(y))")
            
        log_func(f"   Получен итоговый массив весов (первые 5 значений): {[round(x, 2) for x in B_agg[:5]]}")
        log_func(f"   Эти веса показывают, с какой силой итоговый график принадлежит выходной переменной.")
        log_func("")
        return y_univ, B_agg

    def algorithm_3(self, inputs, out_var, imp_type, agg_type, log_func):
        y_univ = self.get_universe(out_var, step=5)
        B_agg = [0.0] * len(y_univ)

        log_func(f"1. ФАЗИФИКАЦИЯ")
        log_func("   Проверяем, насколько текущие показания датчиков соответствуют правилам:")
        for var, val in inputs.items():
            log_func(f"   {var} = {val}")
        
        log_func("")
        log_func(f"2. ЛОГИЧЕСКИЙ ВЫВОД (уровни истинности)")
        
        rule_count = 0
        for rule in self.rules:
            if not all(var in inputs for var, _ in rule['conds']): continue

            alpha = 1.0
            cond_strs = []
            for var, term in rule['conds']:
                val = inputs[var]
                a, b, c = self.terms[var][term]
                mu_val = self.membership(val, a, b, c)
                alpha = min(alpha, mu_val)
                cond_strs.append(f"{var}={term} (степень {mu_val:.2f})")
            
            if alpha > 0:
                rule_count += 1
                B = self.get_set(out_var, rule['out_term'], y_univ)
                
                log_func(f"   Правило: ЕСЛИ {' И '.join(cond_strs)}")
                log_func(f"      Сработало со степенью (минимум из условий): {alpha:.2f}")
                log_func(f"      Вывод правила: {out_var} = {rule['out_term']} (обрезан по уровню {alpha:.2f})")
                
                for j in range(len(y_univ)):
                    if imp_type == 'mamdani': val = min(alpha, B[j])
                    else: val = alpha * B[j]
                    
                    if agg_type == 'max': B_agg[j] = max(B_agg[j], val)
                    else: B_agg[j] = min(1.0, B_agg[j] + val)
                        
        log_func("")
        log_func("3. АГРЕГАЦИЯ (объединение результатов всех правил)")
        if agg_type == 'max':
            log_func("   Оператор агрегации: max (берем максимум по каждому значению выхода).")
            log_func("   Формула: B'(y) = max(B_1(y), B_2(y), ..., B_n(y))")
        else:
            log_func("   Оператор агрегации: sum (алгебраическая сумма).")
            log_func("   Формула: B'(y) = min(1, B_1(y) + B_2(y) + ... + B_n(y))")
            
        log_func(f"   Получен итоговый массив весов (первые 5 значений): {[round(x, 2) for x in B_agg[:5]]}")
        log_func(f"   Эти веса показывают, с какой силой итоговый график принадлежит выходной переменной.")
        log_func("")
        return y_univ, B_agg
        return y_univ, B_agg

    def get_crisp_value(self, y_univ, B, log_func):
        num = sum(y * b for y, b in zip(y_univ, B))
        den = sum(B)
        log_func(f"4. ДЕФАЗИФИКАЦИЯ (перевод графика обратно в число)")
        
        if den == 0: 
            log_func("   Сумма весов равна 0. Система не смогла принять решение.")
            log_func("   Итоговый результат: 0")
            return 0.0
        
        res = num / den
        log_func(f"   Метод центра тяжести: делим площадь под графиком на его ширину.")
        log_func(f"   Сумма (значение X умножить на вес Y) = {num:.2f}")
        log_func(f"   Сумма всех весов Y = {den:.2f}")
        log_func(f"   Итоговый результат: {num:.2f} / {den:.2f} = {res:.2f} секунд полива.")
        return res


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Нечеткая система: Умный полив")
        self.geometry("800x700")
        self.resizable(False, False)

        try:
            self.system = IrrigationSystem("CII_Lab3.txt")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл базы знаний:\n{e}")
            self.destroy()
            return

        self._build_ui()

    def _build_ui(self):
        frame_inputs = ttk.LabelFrame(self, text=" Входные датчики ")
        frame_inputs.pack(fill="x", padx=10, pady=10)

        self.vars = {}
        row = 0
        for var_name, (mn, mx) in self.system.vars.items():
            if var_name == "Water": continue
            
            ttk.Label(frame_inputs, text=f"{var_name}:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
            val_var = tk.DoubleVar(value=(mn+mx)/2)
            self.vars[var_name] = val_var
            
            ttk.Scale(frame_inputs, from_=mn, to=mx, variable=val_var, orient="horizontal", length=300).grid(row=row, column=1, padx=5, pady=5)
            ttk.Label(frame_inputs, textvariable=val_var).grid(row=row, column=2, sticky="w", padx=5, pady=5)
            row += 1

        frame_settings = ttk.Frame(self)
        frame_settings.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_settings, text="Импликация:").pack(side="left")
        self.imp_var = tk.StringVar(value="mamdani")
        ttk.Combobox(frame_settings, textvariable=self.imp_var, values=["mamdani", "larsen"], state="readonly", width=10).pack(side="left", padx=5)

        ttk.Label(frame_settings, text="Агрегация:").pack(side="left", padx=(10,0))
        self.agg_var = tk.StringVar(value="max")
        ttk.Combobox(frame_settings, textvariable=self.agg_var, values=["max", "sum"], state="readonly", width=10).pack(side="left", padx=5)

        ttk.Button(self, text="Рассчитать (3 входа)", command=self._run_multi).pack(pady=5)
        ttk.Button(self, text="Тест (1 вход: Moisture)", command=self._run_single).pack(pady=5)

        self.log_text = tk.Text(self, height=20, font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. Разрешаем стандартные горячие клавиши (на всякий случай)
        self.log_text.bind("<Control-c>", lambda e: self.log_text.event_generate("<<Copy>>"))
        self.log_text.bind("<Control-C>", lambda e: self.log_text.event_generate("<<Copy>>"))

        # 2. Создаем контекстное меню (по правой кнопке мыши)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Копировать", command=lambda: self.log_text.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="Выделить всё", command=lambda: self.log_text.tag_add("sel", "1.0", "end"))
        self.context_menu.add_command(label="Очистить лог", command=lambda: self.log_text.delete("1.0", "end"))

        # 3. Привязываем меню к правой кнопке мыши
        self.log_text.bind("<Button-3>", self._show_context_menu)

    def _log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def _run_single(self):
        self.log_text.delete("1.0", "end")
        moisture = self.vars["Moisture"].get()
        self._log("ТЕСТ 1 ВХОДА (Зависимость полива только от влажности почвы)\n")
        y_u, B = self.system.algorithm_1("Moisture", moisture, "Water", self.imp_var.get(), self.agg_var.get(), self._log)
        self.system.get_crisp_value(y_u, B, self._log)

    def _run_multi(self):
        self.log_text.delete("1.0", "end")
        inputs = {k: v.get() for k, v in self.vars.items()}
        self._log("ТЕСТ 3 ВХОДОВ (Влажность, Температура и Солнце)\n")
        y_u, B = self.system.algorithm_3(inputs, "Water", self.imp_var.get(), self.agg_var.get(), self._log)
        self.system.get_crisp_value(y_u, B, self._log)

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

if __name__ == "__main__":
    App().mainloop()