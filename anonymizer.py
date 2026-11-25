# Анонимайзер — приложение студии «Форма» (учебный проект CDk01).
# Скрывает телефоны, почты и номера карт в любом тексте.
# Работает полностью на вашем компьютере, без интернета.

import re
import tkinter as tk
from tkinter import scrolledtext
from pathlib import Path

# ---------- Правила скрытия данных ----------

# Номер карты: 13-19 цифр, между ними могут быть пробелы и дефисы.
KARTA = re.compile(r'\b\d(?:[ -]?\d){12,18}\b')
# Телефон России: +7 или 8, затем 10 цифр со скобками, пробелами и дефисами.
TELEFON = re.compile(r'(?:\+7|8)\s*\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b')
# Почта: имя, знак @ и домен из букв и точек.
POCHTA = re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', re.IGNORECASE)


def mask_text(text):
    """Заменяет личные данные словами и считает, сколько скрыла."""
    counts = {'карта': 0, 'телефон': 0, 'почта': 0}

    def make_replacement(name):
        def replace(match):
            counts[name] += 1
            return '[' + name + ']'
        return replace

    text = KARTA.sub(make_replacement('карта'), text)
    text = TELEFON.sub(make_replacement('телефон'), text)
    text = POCHTA.sub(make_replacement('почта'), text)
    return text, counts


# ---------- Окно приложения ----------

TSVET_FONA = '#f2efe9'      # светлый тёплый фон
TSVET_PANELI = '#ffffff'    # белые поля
TSVET_KNOPKI = '#2e6b4f'    # зелёная кнопка
TSVET_TEKSTA = '#26251f'


def build_app(root):
    """Создаёт окно и возвращает главные элементы интерфейса."""
    root.title('Анонимайзер')
    root.geometry('760x660')
    try:
        root.iconbitmap(str(Path(__file__).with_name('icon.ico')))
    except Exception:
        pass  # без иконки приложение всё равно работает
    root.configure(bg=TSVET_FONA)

    tk.Label(root, text='Анонимайзер', font=('Segoe UI', 22, 'bold'),
             bg=TSVET_FONA, fg=TSVET_TEKSTA).pack(pady=(18, 2))
    tk.Label(root, text='Скрывает телефоны, почты и номера карт. Данные не покидают компьютер.',
             font=('Segoe UI', 11), bg=TSVET_FONA, fg='#6a675e').pack(pady=(0, 12))

    tk.Label(root, text='Вставьте текст', anchor='w', font=('Segoe UI', 11, 'bold'),
             bg=TSVET_FONA, fg=TSVET_TEKSTA).pack(fill='x', padx=24)
    source = scrolledtext.ScrolledText(root, height=9, wrap='word', font=('Segoe UI', 12),
                                       bg=TSVET_PANELI, fg=TSVET_TEKSTA, relief='flat')
    source.pack(fill='both', expand=True, padx=24, pady=6)

    button_fg = TSVET_TEKSTA if root.tk.call('tk', 'windowingsystem') == 'aqua' else '#ffffff'
    button = tk.Button(root, text='Скрыть данные', font=('Segoe UI', 13, 'bold'),
                       bg=TSVET_KNOPKI, fg=button_fg, activebackground='#245a42',
                       activeforeground=button_fg, relief='flat', padx=18, pady=8, cursor='hand2')

    status = tk.Label(root, text='', font=('Segoe UI', 11), bg=TSVET_FONA, fg=TSVET_TEKSTA)

    def on_click():
        text = source.get('1.0', 'end-1c')
        if not text.strip():
            status.config(text='Сначала вставьте текст — поле пустое.', fg='#9a2424')
            result.delete('1.0', 'end')
            return
        cleaned, counts = mask_text(text)
        result.delete('1.0', 'end')
        result.insert('1.0', cleaned)
        total = sum(counts.values())
        if total == 0:
            status.config(text='Личных данных не найдено — текст не менялся.', fg='#2e6b4f')
        else:
            parts = []
            for name in ('телефон', 'почта', 'карта'):
                if counts[name]:
                    parts.append(f'{name} — {counts[name]}')
            status.config(text='Скрыто: ' + ', '.join(parts) + '.', fg='#2e6b4f')

    button.config(command=on_click)
    button.pack(pady=10)
    status.pack()

    tk.Label(root, text='Результат', anchor='w', font=('Segoe UI', 11, 'bold'),
             bg=TSVET_FONA, fg=TSVET_TEKSTA).pack(fill='x', padx=24, pady=(8, 0))
    result = scrolledtext.ScrolledText(root, height=7, wrap='word', font=('Segoe UI', 12),
                                       bg='#e9e5db', fg=TSVET_TEKSTA, relief='flat')
    result.pack(fill='both', expand=True, padx=24, pady=(6, 16))
    return {'source': source, 'button': button, 'result': result, 'status': status}


def main():
    root = tk.Tk()
    build_app(root)
    root.mainloop()


if __name__ == '__main__':
    main()
