import json
from PIL import Image, ImageDraw, ImageFont

# 罗马音转换表（简化版）
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


class CrosswordGenerator:
    def __init__(self):
        self.grid = {}
        self.problems = []

    def add_problem(self, kanji, std_roma, kana_list, alt_roma, position, direction):
        """添加题目"""
        try:
            kana = kana_list.split(';')
            row, col = self._parse_position(position)
            dr, dc = self._get_direction(direction)

            # 校验和存储
            path = self._validate_path(kana, row, col, dr, dc)
            self._update_grid(kana, path)

            # 保存问题
            self.problems.append({
                "kanji": kanji,
                "std_roma": std_roma,
                "kana": kana,
                "alt_roma": alt_roma.split(';'),
                "position": position.upper(),
                "direction": direction,
                "path": [(r + 1, c + 1) for r, c in path]  # 转为1-based坐标
            })
            return True, "添加成功"
        except Exception as e:
            return False, str(e)

    def generate(self, output_dir="."):
        """生成所有文件"""
        try:
            self._generate_images(output_dir)
            self._save_json(output_dir)
            return True, {
                "kana": f"{output_dir}/crossword_kana.png",
                "romaji": f"{output_dir}/crossword_romaji.png",
                "data": f"{output_dir}/crossword_data.json"
            }
        except Exception as e:
            return False, str(e)

    def _parse_position(self, pos):
        """解析A2格式坐标为(行, 列)"""
        col = ord(pos[0].upper()) - ord('A')
        row = int(pos[1:]) - 1
        return row, col

    def _get_direction(self, dir_str):
        """获取方向向量"""
        directions = {
            "右": (0, 1), "左": (0, -1),
            "下": (1, 0), "上": (-1, 0)
        }
        return directions.get(dir_str, (0, 1))

    def _validate_path(self, kana, row, col, dr, dc):
        """验证路径有效性"""
        path = []
        for i in range(len(kana)):
            r = row + dr * i
            c = col + dc * i
            pos = (r, c)
            if pos in self.grid and self.grid[pos] != kana[i]:
                raise ValueError(f"位置冲突：{pos} 已存在 {self.grid[pos]}")
            path.append(pos)
        return path

    def _update_grid(self, kana, path):
        """更新网格数据"""
        for pos, char in zip(path, kana):
            self.grid[pos] = char

    def _generate_images(self, output_dir):
        """生成两种模式的图片"""
        # 获取网格范围
        rows = [r for r, _ in self.grid.keys()]
        cols = [c for _, c in self.grid.keys()]
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        # 生成两种图片
        self._draw_image("kana", min_row, max_row, min_col, max_col, output_dir)
        self._draw_image("romaji", min_row, max_row, min_col, max_col, output_dir)

    def _draw_image(self, mode, min_row, max_row, min_col, max_col, output_dir):
        """实际绘制图片"""
        cell_size = 40
        padding = 50
        img = Image.new('RGB', (
            (max_col - min_col + 3) * cell_size + padding,
            (max_row - min_row + 3) * cell_size + padding
        ), 'white')
        draw = ImageDraw.Draw(img)

        # 绘制所有格子
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                x = (c - min_col + 1) * cell_size + padding // 2
                y = (r - min_row + 1) * cell_size + padding // 2
                draw.rectangle([x, y, x + cell_size, y + cell_size], outline='black')

                # 填充内容
                if (r, c) in self.grid:
                    text = self.grid[(r, c)]
                    if mode == "romaji":
                        text = ROMAJI_MAP.get(text, '?')
                    draw.text((x + 10, y + 5), text, fill='black')

        # 保存文件
        img.save(f"{output_dir}/crossword_{mode}.png")

    def _save_json(self, output_dir):
        """保存数据文件"""
        with open(f"{output_dir}/crossword_data.json", "w", encoding='utf-8') as f:
            json.dump(self.problems, f, ensure_ascii=False, indent=2)


class CrosswordSolver:
    def __init__(self, data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.user_answers = {}
        self._build_index()

    def _build_index(self):
        """构建答案索引"""
        self.answer_map = {}
        for p in self.data:
            key = (p['position'], p['direction'])
            self.answer_map[key] = {
                'kana': p['kana'],
                'aliases': {p['kanji'], p['std_roma'], ';'.join(p['kana'])} | set(p['alt_roma'])
            }

    def submit(self, position, direction, answer):
        """提交答案"""
        try:
            key = (position.upper(), direction)
            if key not in self.answer_map:
                return False, "题目不存在"

            # 答案校验
            if answer.strip() not in self.answer_map[key]['aliases']:
                return False, "答案错误"

            # 更新填写状态
            self._update_progress(key)
            return True, "答案正确"
        except Exception as e:
            return False, str(e)

    def _update_progress(self, key):
        """更新填写进度"""
        problem = next(p for p in self.data
                       if p['position'] == key[0] and p['direction'] == key[1])
        for pos, kana in zip(problem['path'], problem['kana']):
            self.user_answers[tuple(pos)] = kana

    def generate_progress_image(self, mode="kana", output_dir="."):
        """生成进度图片"""
        # 收集所有位置
        all_positions = {tuple(pos) for p in self.data for pos in p['path']}
        rows = [r for r, _ in all_positions]
        cols = [c for _, c in all_positions]
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        # 创建图片
        cell_size = 40
        padding = 50
        img = Image.new('RGB', (
            (max_col - min_col + 3) * cell_size + padding,
            (max_row - min_row + 3) * cell_size + padding
        ), 'white')
        draw = ImageDraw.Draw(img)

        # 绘制格子
        for pos in all_positions:
            r, c = pos
            x = (c - min_col + 1) * cell_size + padding // 2
            y = (r - min_row + 1) * cell_size + padding // 2
            draw.rectangle([x, y, x + cell_size, y + cell_size], outline='black')

            # 填写内容
            if pos in self.user_answers:
                text = self.user_answers[pos]
                if mode == "romaji":
                    text = ROMAJI_MAP.get(text, '?')
                draw.text((x + 10, y + 5), text, fill='blue')

        # 保存文件
        img.save(f"{output_dir}/progress_{mode}.png")
        return True, f"{output_dir}/progress_{mode}.png"


def print_help():
    """打印帮助信息"""
    print("欢迎使用填字游戏！")
    print("可用命令：")
    print("1. /help - 显示此帮助信息")
    print("2. /选择题目 第X题 - 选择要作答的题目")
    print("3. /作答 坐标 答案 - 提交答案（例如：/作答 B2 い;ぬ;ば;し;り;も;み;じ）")
    print("4. /退出 - 退出游戏")

def main():
    # 创建填字游戏
    generator = CrosswordGenerator()
    generator.add_problem(
        kanji="犬走椛",
        std_roma="inubashiri momiji",
        kana_list="い;ぬ;ば;し;り;も;み;じ",
        alt_roma="inubasiri momiji",
        position="B2",
        direction="右"
    )
    generator.generate()

    # 初始化解答器
    solver = CrosswordSolver("crossword_data.json")
    current_problem = None

    print("填字游戏已启动！输入 /help 查看帮助信息。")

    while True:
        user_input = input("请输入命令：").strip()
        
        if user_input == "/help":
            print_help()
            continue
            
        elif user_input == "/退出":
            print("感谢使用，再见！")
            break
            
        elif user_input.startswith("/选择题目"):
            try:
                problem_num = int(user_input.split()[1])
                if 1 <= problem_num <= len(solver.data):
                    current_problem = solver.data[problem_num - 1]
                    print(f"已选择第{problem_num}题：")
                    print(f"位置：{current_problem['position']}")
                    print(f"方向：{current_problem['direction']}")
                    print(f"汉字：{current_problem['kanji']}")
                else:
                    print("题目编号无效！")
            except (IndexError, ValueError):
                print("请输入正确的题目编号！")
            continue
            
        elif user_input.startswith("/作答"):
            if not current_problem:
                print("请先使用 /选择题目 选择要作答的题目！")
                continue
                
            try:
                _, position, answer = user_input.split(maxsplit=2)
                success, message = solver.submit(position, current_problem['direction'], answer)
                print(message)
                
                if success:
                    solver.generate_progress_image()
                    print("已更新进度图片！")
            except ValueError:
                print("请输入正确的格式：/作答 坐标 答案")
            continue
            
        else:
            print("未知命令！输入 /help 查看帮助信息。")

if __name__ == "__main__":
    main()