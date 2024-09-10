import tkinter as tk
from tkinter import filedialog, messagebox, StringVar  # StringVar를 명시적으로 가져옴
import tkinter.ttk as ttk  # ttk 모듈 임포트
import pandas as pd
import hashlib
import numpy as np


# CSV 파일 병합
def load_csv_1():
    global df1
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            df1 = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df1 = pd.read_csv(file_path, encoding='cp949')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file: {e}")
                return
        listbox_csv1.delete(0, tk.END)
        for column in df1.columns:
            listbox_csv1.insert(tk.END, column)
        highlight_common_keys()

def load_csv_2():
    global df2
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            df2 = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df2 = pd.read_csv(file_path, encoding='cp949')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file: {e}")
                return
        listbox_csv2.delete(0, tk.END)
        for column in df2.columns:
            listbox_csv2.insert(tk.END, column)
        highlight_common_keys()

def highlight_common_keys():
    for i in range(listbox_csv1.size()):
        listbox_csv1.itemconfig(i, bg="white")
    for i in range(listbox_csv2.size()):
        listbox_csv2.itemconfig(i, bg="white")

    if df1 is not None and df2 is not None:
        common_columns = set(df1.columns).intersection(set(df2.columns))
        for i, column in enumerate(df1.columns):
            if column in common_columns:
                listbox_csv1.itemconfig(i, bg="yellow")
        for i, column in enumerate(df2.columns):
            if column in common_columns:
                listbox_csv2.itemconfig(i, bg="yellow")

        key_menu['values'] = list(common_columns)
        if common_columns:
            key_menu.current(0)

def merge_csv():
    if df1 is not None and df2 is not None:
        selected_key = key_menu.get()
        if not selected_key:
            messagebox.showerror("Error", "Please select a key column for merging.")
            return

        df_to_merge = pd.merge(df1, df2, how='outer', on=selected_key)
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            try:
                df_to_merge.to_csv(save_path, sep=",", index=False, encoding='utf-8-sig')
                messagebox.showinfo("Success", f"CSV files merged and saved successfully as {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save the CSV file: {e}")
    else:
        messagebox.showerror("Error", "Please load two CSV files first.")

# 비식별화 관련 함수들
def sha256_text(text):
    text_str = str(text)
    return hashlib.sha256(text_str.encode()).hexdigest()

def mask_name(name):
    if isinstance(name, float) and np.isnan(name):
        return name  # NaN인 경우 처리하지 않음
    name_str = str(name)  # 입력값을 문자열로 변환
    if len(name_str) == 2:
        return name_str[0] + "*"
    elif len(name_str) == 3:
        return name_str[0] + "*" + "*"
    elif len(name_str) == 4:
        return name_str[0] + name_str[1] + "**"
    else:
        return name_str  # 이름의 길이가 맞지 않는 경우 원래 이름 반환


def mask_phone(phone):
    phone_str = str(phone)
    return '0' + phone_str[:2] + '-' + '****' + '-' + phone_str[6:]

def categorize_age(birthdate):
    today = pd.Timestamp.now()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    if age < 20:
        return '10대'
    elif age < 30:
        return '20대'
    elif age < 40:
        return '30대'
    elif age < 50:
        return '40대'
    else:
        return '50대 이상'

def mask_address(address):
    if isinstance(address, float) and np.isnan(address):
        return address  # NaN 값은 그대로 반환
    address_str = str(address)  # 입력값을 문자열로 변환
    parts = address_str.split(' ')
    
    if len(parts) > 1:
        return parts[0] + " " + "****"
    else:
        return address_str  # 주소의 형식이 맞지 않으면 원래 주소 반환


def round_up_square_footage(sq_ft):
    return np.ceil(sq_ft / 100) * 100

def round_up_monthly_payment(payment):
    return np.ceil(payment / 100000) * 100000

# CSV 파일 비식별화
# Tkinter 메인 윈도우 생성
window = tk.Tk()

# TabControl 생성
tabControl = ttk.Notebook(window)

# method_menu 변수 정의
method_menu = StringVar(window)
method_menu.set('')  # 초기값 설정

# 이후에 method_menu를 사용하는 코드
method_menu.set('')


def load_csv_for_anonymize():
    global df_to_anonymize, anonymization_settings
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            df_to_anonymize = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df_to_anonymize = pd.read_csv(file_path, encoding='latin1')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file: {e}")
                return
        
        # 목록 초기화 및 비식별화 설정 초기화
        clear_anonymization_frame()

        anonymization_settings = {}
        for column in df_to_anonymize.columns:
            # 각 속성에 대한 항목을 프레임에 추가
            add_column_with_button(column)
        
        method_menu.set('')

def add_column_with_button(column):
    frame = tk.Frame(anonymize_tab)
    frame.pack(fill=tk.X, pady=2)

    label = tk.Label(frame, text=column)
    label.pack(side=tk.LEFT, padx=5)

    method_menu = ttk.Combobox(frame, state="readonly", values=[
        "Replace with **", "Replace with ***", "SHA-256 Encrypt", "Mask Phone",
        "Categorize Age", "Mask Address", "Round Up Square Footage", "Round Up Monthly Payment"
    ])
    method_menu.pack(side=tk.LEFT, padx=5)

    button = tk.Button(frame, text="Set", command=lambda: set_anonymization(column, method_menu))
    button.pack(side=tk.LEFT, padx=5)

def set_anonymization(column, method_menu):
    selected_method = method_menu.get()
    if selected_method:
        anonymization_settings[column] = selected_method
        update_display()

def clear_anonymization_frame():
    for widget in anonymize_tab.winfo_children():
        if isinstance(widget, tk.Frame):
            widget.destroy()

def update_display():
    settings_listbox.delete(0, tk.END)
    for column, method in anonymization_settings.items():
        settings_listbox.insert(tk.END, f"{column}: {method}")

def anonymize_csv():
    if df_to_anonymize is not None:
        for column_name, method in anonymization_settings.items():
            if method == "Replace with **":
                df_to_anonymize[column_name] = df_to_anonymize[column_name].apply(mask_name)
            elif method == "Replace with ***":
                df_to_anonymize[column_name] = df_to_anonymize[column_name].apply(mask_name)
            elif method == "SHA-256 Encrypt":
                df_to_anonymize[column_name] = df_to_anonymize[column_name].apply(sha256_text)
            elif method == "Mask Phone":
                df_to_anonymize[column_name] = df_to_anonymize[column_name].apply(mask_phone)
            elif method == "Categorize Age":
                df_to_anonymize[column_name] = df_to_anonymize[column_name].apply(categorize_age)
            elif method == "Mask Address":
                df_to_anonymize[column_name] = df_to_anonymize[column_name].apply(mask_address)
            elif method == "Round Up Square Footage":
                df_to_anonymize[column_name] = df_to_anonymize[column_name].apply(round_up_square_footage)
            elif method == "Round Up Monthly Payment":
                df_to_anonymize[column_name] = df_to_anonymize[column_name].apply(round_up_monthly_payment)

        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            df_to_anonymize.to_csv(save_path, index=False)
            messagebox.showinfo("Success", f"CSV file anonymized and saved successfully as {save_path}")
    else:
        messagebox.showerror("Error", "Please load a CSV file first.")

# GUI 설정
root = tk.Tk()
root.title("CSV Tool")
root.geometry("800x600")

tabControl = ttk.Notebook(root)
merge_tab = ttk.Frame(tabControl)
anonymize_tab = ttk.Frame(tabControl)
tabControl.add(merge_tab, text="CSV Merge")
tabControl.add(anonymize_tab, text="Anonymization")
tabControl.pack(expand=1, fill="both")

# Merge Tab
df1 = None
df2 = None

ttk.Button(merge_tab, text="Load CSV 1", command=load_csv_1).pack(pady=5)
listbox_csv1 = tk.Listbox(merge_tab)
listbox_csv1.pack(pady=5, fill=tk.X)

ttk.Button(merge_tab, text="Load CSV 2", command=load_csv_2).pack(pady=5)
listbox_csv2 = tk.Listbox(merge_tab)
listbox_csv2.pack(pady=5, fill=tk.X)

ttk.Label(merge_tab, text="Select Key Column:").pack(pady=5)
key_menu = ttk.Combobox(merge_tab, state="readonly")
key_menu.pack(pady=5)

btn_merge = ttk.Button(merge_tab, text="Merge CSV Files", command=merge_csv)
btn_merge.pack(pady=5)

# Anonymization Tab
df_to_anonymize = None
anonymization_settings = {}
ttk.Button(anonymize_tab, text="Load CSV", command=load_csv_for_anonymize).pack(pady=5)

settings_listbox = tk.Listbox(anonymize_tab)
settings_listbox.pack(pady=5, fill=tk.X)

ttk.Button(anonymize_tab, text="Anonymize CSV", command=anonymize_csv).pack(pady=5)

root.mainloop()
