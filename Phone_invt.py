import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_NAME = 'inventory.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS phones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incoming_date TEXT,
                sale_date TEXT,
                model TEXT,
                storage TEXT,
                cond TEXT,
                purchase_price REAL,
                sale_price REAL,
                quantity INTEGER
                )''')
    conn.commit()
    conn.close()

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Used Phone Inventory Management')
        self.create_main_widgets()

    def create_main_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        add_btn = tk.Button(frame, text='재고 입력', width=20, command=self.open_add_window)
        add_btn.grid(row=0, column=0, pady=5)

        available_btn = tk.Button(frame, text='판매가능 재고 조회', width=20,
                                  command=lambda: self.open_list_window(sold=False))
        available_btn.grid(row=1, column=0, pady=5)

        sold_btn = tk.Button(frame, text='판매 내역 조회', width=20,
                             command=lambda: self.open_list_window(sold=True))
        sold_btn.grid(row=2, column=0, pady=5)

        exit_btn = tk.Button(frame, text='종료', width=20, command=self.root.quit)
        exit_btn.grid(row=3, column=0, pady=5)

    def open_add_window(self):
        InventoryEditor(self.root, refresh=None)

    def open_list_window(self, sold=False):
        ListWindow(self.root, sold)

class InventoryEditor:
    def __init__(self, master, record=None, refresh=None):
        self.master = tk.Toplevel(master)
        self.master.title('재고 입력' if record is None else '재고 수정')
        self.record = record
        self.refresh = refresh
        self.create_widgets()
        if record:
            self.load_record()

    def create_widgets(self):
        labels = ['입고날짜(YYYY-MM-DD)', '판매일자(YYYY-MM-DD)', '모델', '저장공간',
                  '폰상태', '매입가', '판매가', '수량']
        self.entries = {}
        for i, text in enumerate(labels):
            tk.Label(self.master, text=text).grid(row=i, column=0, sticky='e')
            entry = tk.Entry(self.master)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[text] = entry

        btn_text = '추가' if self.record is None else '저장'
        action_btn = tk.Button(self.master, text=btn_text, command=self.save_record)
        action_btn.grid(row=len(labels), column=0, columnspan=2, pady=5)

        if self.record is not None:
            del_btn = tk.Button(self.master, text='삭제', command=self.delete_record)
            del_btn.grid(row=len(labels)+1, column=0, columnspan=2, pady=5)

    def load_record(self):
        labels = ['입고날짜(YYYY-MM-DD)', '판매일자(YYYY-MM-DD)', '모델', '저장공간',
                  '폰상태', '매입가', '판매가', '수량']
        for value, label in zip(self.record[1:], labels):
            self.entries[label].insert(0, '' if value is None else value)

    def get_values(self):
        data = {}
        for label, entry in self.entries.items():
            data[label] = entry.get().strip()
        return data

    def save_record(self):
        data = self.get_values()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.record is None:
            c.execute('''INSERT INTO phones
                         (incoming_date, sale_date, model, storage, cond,
                          purchase_price, sale_price, quantity)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (data['입고날짜(YYYY-MM-DD)'], data['판매일자(YYYY-MM-DD)'],
                       data['모델'], data['저장공간'], data['폰상태'],
                       data['매입가'], data['판매가'], data['수량']))
        else:
            c.execute('''UPDATE phones SET incoming_date=?, sale_date=?, model=?,
                         storage=?, cond=?, purchase_price=?, sale_price=?, quantity=?
                         WHERE id=?''',
                      (data['입고날짜(YYYY-MM-DD)'], data['판매일자(YYYY-MM-DD)'],
                       data['모델'], data['저장공간'], data['폰상태'],
                       data['매입가'], data['판매가'], data['수량'], self.record[0]))
        conn.commit()
        conn.close()
        if self.refresh:
            self.refresh()
        self.master.destroy()

    def delete_record(self):
        if messagebox.askyesno('삭제 확인', '정말로 삭제하시겠습니까?'):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('DELETE FROM phones WHERE id=?', (self.record[0],))
            conn.commit()
            conn.close()
            if self.refresh:
                self.refresh()
            self.master.destroy()

class ListWindow:
    def __init__(self, master, sold=False):
        self.master = tk.Toplevel(master)
        self.sold = sold
        title = '판매가능 재고' if not sold else '판매 내역'
        self.master.title(title)
        self.create_widgets()
        self.load_records()

    def create_widgets(self):
        columns = ('id', 'incoming', 'sale', 'model', 'storage', 'cond', 'buy', 'sell', 'qty')
        self.tree = ttk.Treeview(self.master, columns=columns, show='headings')
        headers = ['ID', '입고날짜', '판매일자', '모델', '저장공간', '폰상태', '매입가', '판매가', '수량']
        for col, head in zip(columns, headers):
            self.tree.heading(col, text=head)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', self.on_double_click)

    def load_records(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.sold:
            c.execute('SELECT * FROM phones WHERE sale_date IS NOT NULL AND sale_date != ""')
        else:
            c.execute('SELECT * FROM phones WHERE sale_date IS NULL OR sale_date = ""')
        rows = c.fetchall()
        conn.close()
        for r in rows:
            self.tree.insert('', tk.END, values=r)

    def on_double_click(self, event):
        item = self.tree.selection()
        if item:
            record = self.tree.item(item)['values']
            InventoryEditor(self.master, record=record, refresh=self.load_records)

if __name__ == '__main__':
    init_db()
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()
