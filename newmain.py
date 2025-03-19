import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw, ImageFont
import json


# 简化的罗马音转换表（不考虑拗音、促音，ん→n）
ROMAJI_MAP = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'si', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'ti', 'つ': 'tu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'hu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'を': 'wo', 'ん': 'n',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'zi', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po'
}

def get_japanese_font(size=20):
    font_candidates = [
        "msgothic.ttc",  # Windows
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",  # MacOS
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"  # Linux
    ]
    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    return ImageFont.load_default()


class CrosswordSolver:
    def __init__(self, data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            self.problems = json.load(f)

        # 构建答案索引
        self.answer_map = {}
        self.all_positions = set()
        for p in self.problems:
            key = (p['position'], p['direction'])

            # 生成所有可能的答案形式
            aliases = {
                p['kanji'],
                p['std_roma'],
                ';'.join(p['kana'])  # 假名列表的分号形式
            }
            aliases.update(p['alt_roma'])

            self.answer_map[key] = {
                'kana': p['kana'],
                'aliases': aliases
            }
            for pos in p['path']:
                self.all_positions.add((pos[0], pos[1]))

        # 初始化用户进度
        self.user_grid = {}
        self.correct_grid = {}
        for p in self.problems:
            for pos, kana in zip(p['path'], p['kana']):
                self.correct_grid[(pos[0], pos[1])] = kana

        # 初始化时添加显示模式状态
        self.display_mode = "kana"  # 或 "romaji"

        # 创建界面
        self.root = tk.Tk()
        self.root.title("填字游戏解答器")
        self.create_widgets()
        self.update_image()
        self.add_toggle_button()  # 添加切换按钮
        # 创建界面后强制更新图片显示
        self.update_image()
        self.root.after(100, self._force_image_refresh)  # 解决Tkinter图片加载问题

    def add_toggle_button(self):
        toggle_frame = ttk.Frame(self.root)
        toggle_frame.grid(row=1, column=0, pady=5)

        self.mode_var = tk.StringVar(value="kana")
        ttk.Radiobutton(toggle_frame, text="假名模式", variable=self.mode_var,
                        value="kana", command=self.toggle_mode).pack(side='left')
        ttk.Radiobutton(toggle_frame, text="罗马音模式", variable=self.mode_var,
                        value="romaji", command=self.toggle_mode).pack(side='left')

    def toggle_mode(self):
        self.display_mode = self.mode_var.get()
        self.update_image()

    def kana_to_romaji(self, kana):
        """简化版假名转罗马音"""
        return ROMAJI_MAP.get(kana, '?')
    def _force_image_refresh(self):
        """强制刷新图片显示"""
        self.img_label.configure(image='')
        self.update_image()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky='nw')

        ttk.Label(frame, text="起始位置（例：A2）:").grid(row=0, column=0, sticky='w')
        self.pos_entry = ttk.Entry(frame, width=10)
        self.pos_entry.grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="方向:").grid(row=1, column=0, sticky='w')
        self.dir_combo = ttk.Combobox(frame, values=["右", "下", "左", "上"], width=5)
        self.dir_combo.current(0)
        self.dir_combo.grid(row=1, column=1, padx=5)

        ttk.Label(frame, text="答案:").grid(row=2, column=0, sticky='w')
        self.ans_entry = ttk.Entry(frame, width=25)
        self.ans_entry.grid(row=2, column=1, padx=5)

        ttk.Button(frame, text="提交答案", command=self.check_answer).grid(row=3, column=0, columnspan=2, pady=10)

        self.img_label = ttk.Label(self.root)
        self.img_label.grid(row=0, column=1, padx=10)

    def parse_position(self, pos_str):
        try:
            col = ord(pos_str[0].upper()) - ord('A')
            row = int(pos_str[1:])
            return (row, col)
        except:
            raise ValueError("无效的位置格式")

    def check_answer(self):
        try:
            position = self.pos_entry.get().upper()
            direction = self.dir_combo.get()
            answer = self.ans_entry.get().strip()

            # 验证基本格式
            start_pos = self.parse_position(position)
            key = (position, direction)

            if key not in self.answer_map:
                raise ValueError("该位置和方向没有对应的题目")

            problem = self.answer_map[key]

            # 检查是否匹配任意别名
            if answer not in problem['aliases']:
                raise ValueError("答案不正确")

            # 更新用户进度
            self.update_user_grid(start_pos, direction, problem['kana'])
            self.update_image()
            messagebox.showinfo("正确", "答案正确！已更新填字表")

        except Exception as e:
            messagebox.showerror("错误", str(e))

    def update_user_grid(self, start_pos, direction, kana_list):
        dir_map = {
            "右": (0, 1),
            "左": (0, -1),
            "下": (1, 0),
            "上": (-1, 0)
        }
        dr, dc = dir_map[direction]

        for i, kana in enumerate(kana_list):
            row = start_pos[0] + dr * i
            col = start_pos[1] + dc * i
            self.user_grid[(row, col)] = kana

    def update_image(self):
        """生成并显示当前模式的图片"""
        # 生成两种图片
        self.generate_image("kana")
        self.generate_image("romaji")

        # 加载当前模式的图片
        filename = f"current_{self.display_mode}.png"
        photo = tk.PhotoImage(file=filename)

        self.img_label.configure(image=photo)
        self.img_label.image = photo

    def generate_image(self, mode):
        """生成指定模式的图片"""
        font = get_japanese_font(20)
        font_small = get_japanese_font(14)

        # 计算网格范围
        rows = [p[0] for p in self.all_positions]
        cols = [p[1] for p in self.all_positions]
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        cell_size = 40
        padding = 50
        img = Image.new('RGB', (
            (max_col - min_col + 3) * cell_size + padding,
            (max_row - min_row + 3) * cell_size + padding
        ), 'white')
        draw = ImageDraw.Draw(img)

        # 绘制网格和内容
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                x = (c - min_col + 1) * cell_size + padding // 2
                y = (r - min_row + 1) * cell_size + padding // 2

                # 绘制格子边框
                draw.rectangle([x, y, x + cell_size, y + cell_size], outline='black')

                # 处理内容显示
                if (r, c) in self.user_grid:
                    text = self.user_grid[(r, c)]
                    display_text = text if mode == "kana" else self.kana_to_romaji(text)
                    draw.text((x + 10, y + 5), display_text, font=font, fill='blue')
                elif (r, c) in self.correct_grid:
                    # 灰色背景表示待填空格
                    draw.rectangle([x + 2, y + 2, x + cell_size - 2, y + cell_size - 2],
                                   fill='#EEEEEE')

        # 添加坐标标签
        for c in range(min_col, max_col + 1):
            x = (c - min_col + 1) * cell_size + padding // 2 + cell_size // 2
            draw.text((x, padding // 4), chr(c + ord('A')), font=font_small, fill='black')

        for r in range(min_row, max_row + 1):
            y = (r - min_row + 1) * cell_size + padding // 2 + cell_size // 2
            draw.text((padding // 4, y), str(r), font=font_small, fill='black')

        img.save(f"current_{mode}.png")
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    CrosswordSolver("crossword_data.json").run()