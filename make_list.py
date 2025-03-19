import tkinter as tk
from tkinter import messagebox , filedialog
import json

# 创建主窗口
root = tk.Tk()
root.title("矩阵字符编辑器")

# 全局变量，用于存储矩阵的行数、列数和表格的 Entry 组件
rows = 0
cols = 0
entries = []


def generate_matrix():
    """根据输入的行数和列数生成表格"""
    global rows, cols, entries

    # 获取用户输入的行数和列数
    try:
        rows = int(row_entry.get())
        cols = int(col_entry.get())
        if rows <= 0 or cols <= 0:
            raise ValueError("行数和列数必须为正整数")
    except ValueError as e:
        messagebox.showerror("输入错误", "请输入有效的行数和列数（正整数）")
        return

    # 清空之前的表格
    for widget in matrix_frame.winfo_children():
        widget.destroy()
    entries.clear()

    # 生成新的表格
    for i in range(rows):
        row_entries = []
        for j in range(cols):
            entry = tk.Entry(matrix_frame, width=3)
            entry.grid(row=i, column=j, padx=5, pady=5)
            row_entries.append(entry)
        entries.append(row_entries)


def save_matrix():
    """保存矩阵并打印结果"""
    global rows, cols, entries

    if not entries:
        messagebox.showwarning("无数据", "请先生成矩阵")
        return

    matrix = []
    for i in range(rows):
        row = []
        for j in range(cols):
            value = entries[i][j].get()
            row.append([value,0])
        matrix.append(row)
    height = len(matrix)
    weight = len(matrix[0])
    print(height,weight)
    # 打印矩阵
    print("当前矩阵内容：")
    for row in matrix:
        print(row)
    messagebox.showinfo("保存成功", "矩阵已保存")



    #print(matrix)
    save_to_json(matrix,"answer")







# 将列表存入 JSON 文件　
def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"数据已保存到 {filename}")


# 从 JSON 文件读取列表
def load_from_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"从 {filename} 读取的数据：")
    print(data)
    return data




# tk ui 部分

def browse_path():
    """打开文件选择对话框"""
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, path)


# 输入行数和列数的部分
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

tk.Label(input_frame, text="行数：").grid(row=0, column=0, padx=5, pady=5)
row_entry = tk.Entry(input_frame)
row_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(input_frame, text="列数：").grid(row=0, column=2, padx=5, pady=5)
col_entry = tk.Entry(input_frame)
col_entry.grid(row=0, column=3, padx=5, pady=5)

generate_button = tk.Button(input_frame, text="生成矩阵", command=generate_matrix)
generate_button.grid(row=0, column=4, padx=10, pady=5)

# 矩阵显示部分
matrix_frame = tk.Frame(root)
matrix_frame.pack(pady=3)

# 保存按钮
save_button = tk.Button(root, text="保存矩阵", command=save_matrix)
save_button.pack(pady=10)

path_frame = tk.Frame(root)
path_frame.pack(pady=10)

tk.Label(path_frame, text="保存路径：").pack(side=tk.LEFT, padx=5)
path_entry = tk.Entry(path_frame, width=40)
path_entry.pack(side=tk.LEFT, padx=5)
browse_btn = tk.Button(path_frame, text="浏览", command=browse_path)
browse_btn.pack(side=tk.LEFT, padx=5)


# 放个说明
l = tk.Label(root, text='先生成，再保存，每个框写一个字符', bg='red', font=('Arial', 12), width=30, height=2)
l.pack()

# 运行主循环
root.mainloop()