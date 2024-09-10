import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import pandas as pd
import hashlib
import numpy as np
import chardet  # 인코딩 감지를 위해 추가


# 전역 변수
df1 = None
df2 = None
df_to_anonymize = None
anonymization_settings = {}
anonymized_columns = []


def detect_encoding(file_path):
    """파일의 인코딩을 자동으로 감지하여 반환하는 함수"""
    with open(file_path, 'rb') as file:
        result = chardet.detect(file.read())
    return result['encoding']


def load_csv(file_path):
    """파일을 적절한 인코딩으로 로드하는 함수"""
    encodings = ['utf-8', 'cp949', 'latin1']
    for enc in encodings:
        try:
            return pd.read_csv(file_path, encoding=enc)
        except UnicodeDecodeError:
            continue

    # 모든 기본 인코딩이 실패한 경우, 자동 인코딩 탐지 시도
    try:
        encoding = detect_encoding(file_path)
        return pd.read_csv(file_path, encoding=encoding)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load CSV file: {e}")
        return None


def load_csv_1():
    global df1
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        df1 = load_csv(file_path)
        if df1 is not None:
            listbox_csv1.delete(0, tk.END)
            for column in df1.columns:
                listbox_csv1.insert(tk.END, column)
            highlight_common_keys()


def load_csv_2():
    global df2
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        df2 = load_csv(file_path)
        if df2 is not None:
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
        return name
    name_str = str(name)
    if len(name_str) == 2:
        return name_str[0] + "*"
    elif len(name_str) == 3:
        return name_str[0] + "*" + "*"
    elif len(name_str) == 4:
        return name_str[0] + name_str[1] + "**"
    else:
        return name_str


def mask_phone(phone):
    phone_str = str(phone)
    return '0' + phone_str[:2] + '-' + '****' + '-' + phone_str[6:]


def categorize_age(birthdate):
    if isinstance(birthdate, float) and np.isnan(birthdate):
        return birthdate  # 결측값인 경우 그대로 반환

    try:
        birthdate = pd.to_datetime(birthdate)
    except (ValueError, TypeError):
        return 'Invalid Date'  # 잘못된 날짜 형식인 경우 반환

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
        return address
    address_str = str(address)
    parts = address_str.split(' ')

    if len(parts) > 1:
        return parts[0] + " " + "****"
    else:
        return address_str


def round_up_square_footage(sq_ft):
    return np.ceil(sq_ft / 100) * 100


def round_up_monthly_payment(payment):
    return np.ceil(payment / 100000) * 100000


# CSV 파일 비식별화
def anonymize_csv():
    if df_to_anonymize is not None and anonymization_settings:
        # 비식별화 작업 전에 비식별화할 항목들을 CSV로 저장
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            save_path_anonymized_columns = save_path.replace('.csv', '_anonymized_columns.csv')
            try:
                df_to_anonymize[anonymized_columns].to_csv(save_path_anonymized_columns, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Success", f"Original columns saved successfully as {save_path_anonymized_columns}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save the original columns CSV file: {e}")
                return

            # 비식별화 작업 수행
            df_anonymized = df_to_anonymize.copy()

            for column_name, method in anonymization_settings.items():
                if method == "Replace with **":
                    df_anonymized[column_name] = df_to_anonymize[column_name].apply(lambda x: '**' if pd.notna(x) else x)
                elif method == "Replace with ***":
                    df_anonymized[column_name] = df_to_anonymize[column_name].apply(lambda x: '***' if pd.notna(x) else x)
                elif method == "SHA-256 Encrypt":
                    df_anonymized[column_name] = df_to_anonymize[column_name].apply(sha256_text)
                elif method == "Mask Phone":
                    df_anonymized[column_name] = df_to_anonymize[column_name].apply(mask_phone)
                elif method == "Categorize Age":
                    df_anonymized[column_name] = df_to_anonymize[column_name].apply(categorize_age)
                elif method == "Mask Address":
                    df_anonymized[column_name] = df_to_anonymize[column_name].apply(mask_address)
                elif method == "Round Up Square Footage":
                    df_anonymized[column_name] = df_to_anonymize[column_name].apply(round_up_square_footage)
                elif method == "Round Up Monthly Payment":
                    df_anonymized[column_name] = df_to_anonymize[column_name].apply(round_up_monthly_payment)

            # 비식별화된 CSV 파일 저장
            save_path_anonymized = save_path.replace('.csv', '_anonymized.csv')
            try:
                df_anonymized.to_csv(save_path_anonymized, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Success", f"Anonymized CSV file saved successfully as {save_path_anonymized}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save the anonymized CSV file: {e}")
        else:
            messagebox.showerror("Error", "Save path not specified.")
    else:
        messagebox.showerror("Error", "Please load a CSV file first.")




def load_csv_for_anonymize():
    global df_to_anonymize, anonymization_settings, anonymized_columns
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        df_to_anonymize = load_csv(file_path)
        if df_to_anonymize is not None:
            # 목록 초기화 및 비식별화 설정 초기화
            clear_anonymization_frame()

            anonymization_settings = {}
            anonymized_columns = []

            for column in df_to_anonymize.columns:
                # 각 속성에 대한 항목을 프레임에 추가
                add_column_with_button(column)

            # 비식별화할 속성만 모아서 CSV로 저장
            save_anonymized_columns()


def add_column_with_button(column):
    frame = tk.Frame(anonymize_tab)
    frame.pack(fill=tk.X, pady=2)

    label = tk.Label(frame, text=column)
    label.pack(side=tk.LEFT, padx=5)

    method_menu = ttk.Combobox(frame, state="readonly", values=[
        "Replace with **", "Replace with ***", "SHA-256 Encrypt", "Mask Phone",
        "Categorize Age", "Mask Address", "Round Up Square Footage", "Round Up Monthly Payment"])
    method_menu.pack(side=tk.LEFT, padx=5)

    button_add = tk.Button(frame, text="Add", command=lambda c=column: add_column_for_anonymization(c, method_menu))
    button_add.pack(side=tk.LEFT, padx=5)


def clear_anonymization_frame():
    for widget in anonymize_tab.winfo_children():
        if isinstance(widget, tk.Frame):
            widget.destroy()


def add_column_for_anonymization(column_name, method_menu):
    method = method_menu.get()
    if column_name and method:
        anonymization_settings[column_name] = method
        anonymized_columns.append(column_name)
        settings_listbox.insert(tk.END, f"{column_name}: {method}")


# def save_anonymized_columns():
#    if df_to_anonymize is not None and anonymized_columns:
#        save_path_anonymized_columns = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
#        if save_path_anonymized_columns:
#            try:
#                df_to_anonymize[anonymized_columns].to_csv(save_path_anonymized_columns, index=False)
#                messagebox.showinfo("Success", f"Original columns saved successfully as {save_path_anonymized_columns}")
#            except Exception as e:
#                messagebox.showerror("Error", f"Failed to save the CSV file: {e}")


def perform_anonymization():
    if df_to_anonymize is not None and anonymization_settings:
        df_anonymized = df_to_anonymize.copy()

        for column, method in anonymization_settings.items():
            if method == "Replace with **":
                df_anonymized[column] = df_anonymized[column].apply(mask_name)
            elif method == "Replace with ***":
                df_anonymized[column] = df_anonymized[column].apply(mask_name)
            elif method == "SHA-256 Encrypt":
                df_anonymized[column] = df_anonymized[column].apply(sha256_text)
            elif method == "Mask Phone":
                df_anonymized[column] = df_anonymized[column].apply(mask_phone)
            elif method == "Categorize Age":
                df_anonymized[column] = df_anonymized[column].apply(categorize_age)
            elif method == "Mask Address":
                df_anonymized[column] = df_anonymized[column].apply(mask_address)
            elif method == "Round Up Square Footage":
                df_anonymized[column] = df_anonymized[column].apply(round_up_square_footage)
            elif method == "Round Up Monthly Payment":
                df_anonymized[column] = df_anonymized[column].apply(round_up_monthly_payment)

        save_path_anonymized = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path_anonymized:
            try:
                df_anonymized.to_csv(save_path_anonymized, index=False)
                messagebox.showinfo("Success", f"Anonymized CSV saved successfully as {save_path_anonymized}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save the anonymized CSV file: {e}")


# GUI 설정
window = tk.Tk()
window.title("CSV Merger and Anonymizer")
window.geometry("1000x600")
window.grid_rowconfigure(0, weight=1)
window.grid_columnconfigure(0, weight=1)

tab_parent = ttk.Notebook(window)
merge_tab = ttk.Frame(tab_parent)
anonymize_tab = ttk.Frame(tab_parent)
tab_parent.add(merge_tab, text="Merge CSVs")
tab_parent.add(anonymize_tab, text="Anonymize CSV")
tab_parent.pack(expand=1, fill='both')

# Merge CSV UI
frame_csv1 = tk.Frame(merge_tab)
frame_csv1.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
frame_csv1.grid_rowconfigure(1, weight=1)
frame_csv1.grid_columnconfigure(0, weight=1)

frame_csv2 = tk.Frame(merge_tab)
frame_csv2.grid(row=0, column=2, padx=10, pady=10, sticky="nswe")
frame_csv2.grid_rowconfigure(1, weight=1)
frame_csv2.grid_columnconfigure(0, weight=1)

label_csv1 = tk.Label(frame_csv1, text="CSV 1 Columns")
label_csv1.grid(row=0, column=0)

label_csv2 = tk.Label(frame_csv2, text="CSV 2 Columns")
label_csv2.grid(row=0, column=0)

listbox_csv1 = tk.Listbox(frame_csv1)
listbox_csv1.grid(row=1, column=0, sticky="nswe")

listbox_csv2 = tk.Listbox(frame_csv2)
listbox_csv2.grid(row=1, column=0, sticky="nswe")

scrollbar_csv1 = tk.Scrollbar(frame_csv1, orient=tk.VERTICAL, command=listbox_csv1.yview)
scrollbar_csv1.grid(row=1, column=1, sticky="ns")
listbox_csv1.configure(yscrollcommand=scrollbar_csv1.set)

scrollbar_csv2 = tk.Scrollbar(frame_csv2, orient=tk.VERTICAL, command=listbox_csv2.yview)
scrollbar_csv2.grid(row=1, column=1, sticky="ns")
listbox_csv2.configure(yscrollcommand=scrollbar_csv2.set)

btn_load_csv1 = tk.Button(merge_tab, text="Load CSV 1", command=load_csv_1)
btn_load_csv1.grid(row=1, column=0, padx=10, pady=5)

btn_load_csv2 = tk.Button(merge_tab, text="Load CSV 2", command=load_csv_2)
btn_load_csv2.grid(row=1, column=2, padx=10, pady=5)

key_menu_label = tk.Label(merge_tab, text="Select Key Column:")
key_menu_label.grid(row=2, column=0, columnspan=3)

key_menu = ttk.Combobox(merge_tab, state="readonly")
key_menu.grid(row=3, column=0, columnspan=3)

btn_merge = tk.Button(merge_tab, text="Merge CSVs", command=merge_csv)
btn_merge.grid(row=4, column=0, columnspan=3, pady=10)

# Anonymize CSV UI
frame_anonymize = tk.Frame(anonymize_tab)
frame_anonymize.pack(side=tk.TOP, fill=tk.X)

btn_load_csv_anonymize = tk.Button(frame_anonymize, text="Load CSV to Anonymize", command=load_csv_for_anonymize)
btn_load_csv_anonymize.pack(side=tk.LEFT, padx=10, pady=10)

settings_listbox = tk.Listbox(anonymize_tab)
settings_listbox.pack(fill=tk.BOTH, expand=True)

scrollbar_settings = tk.Scrollbar(anonymize_tab, orient=tk.VERTICAL, command=settings_listbox.yview)
scrollbar_settings.pack(side=tk.RIGHT, fill=tk.Y)
settings_listbox.configure(yscrollcommand=scrollbar_settings.set)

btn_anonymize = tk.Button(anonymize_tab, text="Perform Anonymization", command=perform_anonymization)
btn_anonymize.pack(side=tk.BOTTOM, pady=10)

window.mainloop()
