import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw, ImageFont
import json


class CrosswordGenerator:
    
    def __init__(self):
        self.entries = []
        self.grid = {}
        self.problems = []

        # 初始化界面
        self.root = tk.Tk()
        self.root.title("东方填字游戏")
        self.create_interface()

        # 预览画布
        self.canvas = tk.Canvas(self.root, width=400, height=300, bg='white')
        self.canvas.grid(row=0, column=2, rowspan=6, padx=10)

    def create_interface(self):
        # 输入区域
        inputs = [
            ("汉字（例：犬走椛）", "kanji"),
            ("官方罗马音（例：inubashiri momiji）", "std_roma"),
            ("假名列表（分号分隔，例：い;ぬ;ば;し;り;も;み;じ）", "kana_list"),
            ("非官方罗马音变体（分号分隔）", "alt_roma"),
            ("起始坐标（例：A2）", "position"),
            ("方向", "direction")
        ]

        for i, (label, _) in enumerate(inputs):
            tk.Label(self.root, text=label).grid(row=i, column=0, sticky='w')

        # 输入框
        self.kanji = tk.Entry(self.root, width=25)
        self.std_roma = tk.Entry(self.root, width=25)
        self.kana_list = tk.Entry(self.root, width=25)
        self.alt_roma = tk.Entry(self.root, width=25)
        self.position = tk.Entry(self.root, width=10)

        self.kanji.grid(row=0, column=1, pady=2)
        self.std_roma.grid(row=1, column=1, pady=2)
        self.kana_list.grid(row=2, column=1, pady=2)
        self.alt_roma.grid(row=3, column=1, pady=2)
        self.position.grid(row=4, column=1, pady=2, sticky='w')

        # 方向选择
        self.direction = ttk.Combobox(self.root,
                                      values=["右", "下", "左", "上"],
                                      width=5)
        self.direction.grid(row=5, column=1, pady=2, sticky='w')
        self.direction.current(0)

        # 控制按钮
        tk.Button(self.root, text="添加词语", command=self.add_entry,
                  bg='#4CAF50', fg='white').grid(row=6, column=0, pady=10)
        tk.Button(self.root, text="生成填字游戏", command=self.generate,
                  bg='#2196F3', fg='white').grid(row=6, column=1, pady=10)

    def parse_kana(self):
        """解析假名列表"""
        kana = self.kana_list.get().split(';')
        if not all(k.strip() for k in kana):
            raise ValueError("假名列表不能有空元素")
        return kana

    def parse_position(self, pos):
        """解析坐标（如A2 → (1,0)）"""
        try:
            col = ord(pos[0].upper()) - ord('A')
            row = int(pos[1:]) - 1
            return (row, col)
        except:
            raise ValueError("坐标格式错误，示例：A2")

    def add_entry(self):
        try:
            # 获取输入
            kana = self.parse_kana()
            row, col = self.parse_position(self.position.get())
            direction = self.direction.get()

            # 确定方向向量
            dir_map = {
                "右": (0, 1),
                "左": (0, -1),
                "下": (1, 0),
                "上": (-1, 0)
            }
            dr, dc = dir_map[direction]
            

            # 检查冲突
            path = []
            for i, char in enumerate(kana):
                r = row + dr * i
                c = col + dc * i
                pos = (r, c)

                if pos in self.grid:
                    if self.grid[pos] != char:
                        raise ValueError(f"位置冲突：{pos} 已存在 {self.grid[pos]}")
                path.append(pos)

            # 更新网格
            for pos, char in zip(path, kana):
                self.grid[pos] = char

            # 保存记录
            self.problems.append({
                "kanji": self.kanji.get(),
                "std_roma": self.std_roma.get(),
                "kana": kana,
                "alt_roma": self.alt_roma.get().split(';'),
                "position": self.position.get().upper(),
                "direction": direction,
                "path": [(r + 1, c) for r, c in path]  # 转换为1-based坐标
            })

            # 清空输入
            self.kanji.delete(0, tk.END)
            self.std_roma.delete(0, tk.END)
            self.kana_list.delete(0, tk.END)
            self.alt_roma.delete(0, tk.END)
            self.position.delete(0, tk.END)

            # 更新预览
            self.update_preview()
            messagebox.showinfo("成功", "已添加词语并更新预览！")

        except Exception as e:
            messagebox.showerror("输入错误", str(e))

    def update_preview(self):
        """实时预览网格"""
        self.canvas.delete("all")

        # 计算网格范围
        rows = [r for r, _ in self.grid.keys()]
        cols = [c for _, c in self.grid.keys()]
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        # 绘制设置
        cell_size = 30
        start_x, start_y = 50, 50

        # 绘制网格
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                x = start_x + (c - min_col) * cell_size
                y = start_y + (r - min_row) * cell_size

                # 绘制单元格
                self.canvas.create_rectangle(
                    x, y, x + cell_size, y + cell_size,
                    outline='gray'
                )

                # 填写内容
                if (r, c) in self.grid:
                    self.canvas.create_text(
                        x + cell_size / 2, y + cell_size / 2,
                        text=self.grid[(r, c)],
                        font=('Arial', 12)
                    )

        # 绘制坐标标签
        for i, c in enumerate(range(min_col, max_col + 1)):
            x = start_x + i * cell_size + cell_size / 2
            self.canvas.create_text(x, start_y - 20,
                                    text=chr(c + ord('A')))

        for i, r in enumerate(range(min_row, max_row + 1)):
            y = start_y + i * cell_size + cell_size / 2
            self.canvas.create_text(start_x - 30, y, text=str(r + 1))

    def generate(self):
        """生成最终结果"""
        # 创建高清图片
        img = Image.new('RGB', (800, 600), 'white')
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("msgothic.ttc", 20)

        # 计算网格范围
        rows = [r for r, _ in self.grid.keys()]
        cols = [c for _, c in self.grid.keys()]
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        # 绘制设置
        cell_size = 40
        start_x, start_y = 100, 100

        # 绘制网格
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                x = start_x + (c - min_col) * cell_size
                y = start_y + (r - min_row) * cell_size

                draw.rectangle([x, y, x + cell_size, y + cell_size],
                               outline='black')

                if (r, c) in self.grid:
                    draw.text((x + 10, y + 5), self.grid[(r, c)],
                              font=font, fill='black')

        # 保存文件
        img.save("crossword.png")
        with open("crossword_data.json", "w", encoding='utf-8') as f:
            json.dump(self.problems, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("完成", "生成成功！\ncrossword.png\ncrossword_data.json")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    CrosswordGenerator().run()