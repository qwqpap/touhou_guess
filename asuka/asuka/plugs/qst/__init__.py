from nonebot import get_plugin_config, on_command
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from .config import Config
import re
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import sys

PASSWORD = "ayanami"

# 在文件开头添加
PIC_DIR = Path(__file__).parent / "pic"
os.makedirs(str(PIC_DIR), exist_ok=True)

# 设置字体和渲染相关的常量
FONTS_DIR = Path(__file__).parent / "fonts"
FONT_PATHS = {
    'windows': [
        'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
        'C:/Windows/Fonts/YuGothM.ttc',  # 游黑体
        'C:/Windows/Fonts/msgothic.ttc',  # MS Gothic
    ],
    'linux': [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    ],
    'darwin': [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
    ],
    'fallback': str(FONTS_DIR / "NotoSansCJK-Regular.ttc")
}

FONT_SIZE = 15
ROMAJI_FONT_SIZE = 10
CELL_SIZE = 20
GRID_COLOR = "#000000"
BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#000000"
COORDINATE_COLOR = "#666666"
PADDING = 20

# 确保字体目录存在
os.makedirs(str(FONTS_DIR), exist_ok=True)

def get_system_font() -> str:
    """获取系统可用的中日文字体"""
    platform = sys.platform
    if platform.startswith('win'):
        font_paths = FONT_PATHS['windows']
    elif platform.startswith('linux'):
        font_paths = FONT_PATHS['linux']
    elif platform.startswith('darwin'):
        font_paths = FONT_PATHS['darwin']
    else:
        font_paths = []

    # 检查系统字体是否可用
    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path

    # 如果系统字体都不可用，下载并使用 Noto Sans CJK
    fallback_font = FONT_PATHS['fallback']
    if not os.path.exists(fallback_font):
        try:
            import requests
            print("Downloading Noto Sans CJK font...")
            # 使用 Noto Sans CJK SC (简体中文版本)
            font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJK-Regular.ttc"
            response = requests.get(font_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(fallback_font, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for data in response.iter_content(chunk_size=4096):
                        downloaded += len(data)
                        f.write(data)
                        done = int(50 * downloaded / total_size)
                        sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                        sys.stdout.flush()
            print("\nFont downloaded successfully!")
        except Exception as e:
            print(f"Warning: Could not download font: {e}")
            return None
    return fallback_font

# 获取可用的字体路径
FONT_PATH = get_system_font()
if not FONT_PATH:
    print("Warning: No suitable font found. Text rendering might be incorrect.")

__plugin_meta__ = PluginMetadata(
    name="qst",
    description="填字游戏系统",
    usage="使用 /help 查看使用说明",
    config=Config,
)

config = get_plugin_config(Config)

# 放罗马音和假名的映射


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
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'ゐ': 'wi', 'ゑ': 'we', 'ゔ': 'vu'
}



# 存储用户当前选择的题目
user_questions = {}

# 题目布局数据结构
# 格式：{题号: (网格大小, 是否支持假名, [(方向, 内部坐标, 长度, 题号显示, 答案列表), ...])}
crossword_layouts: Dict[int, Tuple[Tuple[int, int], bool, List[Tuple[str, str, int, str, List[str]]]]] = {
    1: (
        (20,20),  # 网格大小 (行数, 列数)
        True,  # 支持假名转换
                [
            ("横", "B1", 5, "1", ["そんびてん", "sonbiten", "孙美天"]),  # 横向用数字1,2,3...
            ("横", "C9", 7, "2", ["こめいじこいし", "komeizikoisi", "komeijikoishi", "古明地恋"]),  
            ("横", "E3", 7, "3", ["いざよいさくや", "izayoisakuya", "十六夜咲夜"]),  
            ("横", "E11", 9, "4", ["とよさとみみのみこ", "toyosatomiminomiko", "丰聪耳神子"]),  
            ("横", "G5", 7, "5", ["むらさみなみつ", "murasaminamitu", "murasaminamitsu", "村纱水蜜"]),  
            ("横", "G14", 6, "6", ["やさかかなこ", "yasakakanako", "八坂神奈子"]),  
            ("横", "I2", 7, "7", ["よりがみしおん", "yorigamision", "yorigamishion", "依神紫苑"]),  
            ("横", "I12", 7, "8", ["ていれいだまい", "teireidamai", "丁礼田舞"]),  
            ("横", "L5", 7, "9", ["くろだにやまめ", "kurodaniyamame", "黑谷山女"]),  
            ("横", "M11", 5, "10", ["かざみゆか", "kazamiyuka", "风见幽香"]),  
            ("横", "O6", 13, "11", ["れいせんうどんげいんいなば", "reisenudongeininaba", "铃仙优昙华院因幡"]),  
            ("横", "S13", 7, "12", ["ひななゐてんし", "hinanawitensi", "hinanaitensi", "hinanawitenshi", "hinanaitenshi", "比那名居天子"]),  

            ("竖", "B1", 6, "一", ["そがのとじこ", "soganotoziko", "soganotojiko", "苏我屠自古"]),  # 竖向用一,二,三...
            ("竖", "A3", 6, "二", ["えびすえいか", "ebisueika", "戎璎花"]),  
            ("竖", "A5", 7, "三", ["こんぱくようむ", "konpakuyoumu", "魂魄妖梦"]),  
            ("竖", "I7", 7, "四", ["おくのだみよい", "okunodamiyoi", "奥野田美宵"]),  
            ("竖", "C9", 6, "五", ["こちやさなえ", "kotiyasanae", "kochiyasanae", "东风谷早苗"]),  
            ("竖", "J9", 9, "六", ["はにやすしんけいき", "haniyasusinkeiki", "haniyasushinkeiki", "埴安神袿姬"]),  
            ("竖", "K11", 9, "七", ["ひめかいどうはたて", "himekaidouhatate", "姬海棠果", "姬海棠极"]),
            ("竖", "A13", 6, "八", ["くろこまさき", "kurokomasaki", "骊驹早鬼"]),
            ("竖", "I13", 9, "九", ["いまいずみかげろう", "imaizumikagerou", "今泉影狼"]),
            ("竖", "I15", 7, "十", ["いばらきかせん", "ibarakikasen", "茨木华扇"]),
            ("竖", "O16", 5, "十一", ["いなばてゐ", "inabatewi", "inabatei", "因幡天为", "因幡帝"]),
            ("竖", "D17", 7, "十二", ["おのづかこまち", "onodukakomati", "onodzukakomati", "onozukakomati", "onodukakomachi", "onodzukakomachi", "onozukakomachi", "小野塚小町", "小野冢小町"]), 

            # ... 添加更多单词
        ]
# 不要加空格或点。罗马音写平文式或训令式都行，但是不要杂交。注意全部是小写字母。ぢ、づ、ゐ、ゑ、を这几个假名的拼写见仁见智。中文写全名，已考虑不同译名。


    ),
    # ... 其他题目
    2: (
        (26,20),  # 网格大小 (行数, 列数)
        False,  # 不支持假名转换
        [
             # 横向用数字1,2,3...
            ("横", "C3", 8, "1", ["月之妖鸟化猫之幻"]),  # 竖向用一,二,三...
            ("横", "F1", 5, "2", ["东方林籁庵"]),  # 横向用数字1,2,3...
            ("横","F7",4,"3",["幽灵乐团"]),
            ("横","F16",3,"4",["背德汉"]),
            ("横","I14",5,"5",["天空的花都"]),
            ("横","J1",3,"6",["学漫才"]),
            ("横","J8",7,"7",["月有丛云花有风"]),
            ("横","L14",7,"8",["光魔魔法银河系"]),
            ("横","O8",7,"9",["炎符废佛的炎风"]),
            ("横","P14",7,"10",["神明后裔的亡灵"]),
            ("横","S4",7,"11",["永远的三日天下"]),
            ("横","S13",4,"12",["圣德传说"]),
            ("横","W1",6,"13",["双姬蓬莱物语"]),
            ("竖", "F1", 6, "一", ["东方文化学刊"]), 
            ("竖", "B3", 5, "二", ["满月的竹林"]), 
            ("竖", "C5", 2, "三", ["妖兽"]), 
            ("竖", "S5", 6, "四", ["远野幻想物语"]), 
            ("竖", "S7", 3, "五", ["三月精"]), 
            ("竖", "E8", 9, "六", ["神灵附体的月之公主"]), 
            ("竖","A10",6,"七",["京都幻想剧团"]),
            ("竖", "M10", 10, "八", ["废线废弃车站下车之旅"]), 
            ("竖", "I12", 9, "九", ["开花爷爷小白的灰烬"]), 
            ("竖", "I14", 4, "十", ["天风之光"]), 
            ("竖", "O14", 5, "十一", ["风神之神德"]),
            ("竖", "E17", 5, "十二", ["豪德寺三花"]),
            ("竖", "L18", 3, "十三", ["银木犀"]),
            ("竖", "O20", 2, "十四", ["瑞灵"]),

            
            
        ]
    ),
    3: (
        (1, 1),  # 网格大小 (行数, 列数)
        False,  # 不支持假名转换
        [
            ("横", "A1", 7, "1", ["3,2,6,9,7,7,7"]),  # 数字序列题目
        ]
    )
}


# 方向映射
DIRECTIONS = {
    "横": "horizontal",
    "竖": "vertical",
    "→": "horizontal",
    "↓": "vertical",
    "h": "horizontal",
    "v": "vertical"
}

# 中文数字映射
chinese_nums = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '千': 1000, '万': 10000
}

def convert_chinese_num(chinese_str: str) -> int:
    result = 0
    temp = 0
    for char in chinese_str:
        if char in chinese_nums:
            if chinese_nums[char] >= 10:
                if temp == 0:
                    temp = 1
                result += temp * chinese_nums[char]
                temp = 0
            else:
                temp = chinese_nums[char]
    if temp:
        result += temp
    return result

# 第三题的答案
NUMBER_SEQUENCE_ANSWER = "2,2,6,9,7,7,7"  

def validate_answer(grid_num: int, question_num: str, answer: str) -> Tuple[bool, str, str]:
    """验证答案是否正确，返回(是否正确, 反馈消息, 用于显示的假名)"""
    # 处理第三题
    if grid_num == 3:
        # 处理中文和英文逗号
        user_answer = answer.replace('，', ',').strip()
        # 检查格式是否正确
        if not all(c.isdigit() or c == ',' for c in user_answer):
            return False, "答案格式错误，请使用逗号分隔的数字序列", ""
        # 检查数字数量
        numbers = [n.strip() for n in user_answer.split(',')]
        if len(numbers) != 7:
            return False, "答案必须包含7个数字，用逗号分隔", ""
        # 检查是否匹配
        if user_answer == NUMBER_SEQUENCE_ANSWER:
            return True, "回答正确！", NUMBER_SEQUENCE_ANSWER
        return False, "回答错误，请重试", ""
    
    # 处理填字题目
    if grid_num not in crossword_layouts:
        return False, f"题目 {grid_num} 不存在", ""
    
    _, _, layout = crossword_layouts[grid_num]
    for direction, start_coord, length, q_num, answers in layout:
        if q_num == question_num:
            # 检查答案长度
            if len(answer) != length:
                return False, f"答案长度错误，需要{length}个字符", ""
            
            # 如果是第二题，只检查长度和交叉验证
            if grid_num == 2:
                return True, "答案已填入，请继续完成其他题目或使用 /提交 提交答案", answer
            
            # 其他题目正常验证
            if any(answer.lower() == valid_answer.lower() for valid_answer in answers):
                return True, "回答正确！", answers[0]  # 返回假名形式
            return False, "回答错误，请重试", ""
    
    return False, f"题号 {question_num} 不存在", ""

help_cmd = on_command("help", priority=10, block=True)
select_cmd = on_command("选择题目", priority=10, block=True)
answer_cmd = on_command("作答", priority=10, block=True)
admin_cmd = on_command("admin", priority=10, block=True)
convert_cmd = on_command("转换", priority=10, block=True)
pass_cmd = on_command("pass", priority=10, block=True)
submit_cmd = on_command("提交", priority=10, block=True)

@help_cmd.handle()
async def handle_help():
    help_text = """填字游戏使用说明：
1. 使用 /选择题目 第X题 来选择要回答的题目（支持中文数字，如：第一题）
2. 使用 /作答 题号 答案 来提交答案
   - 横向题目用数字表示：1, 2, 3...
   - 竖向题目用中文数字表示：一, 二, 三...
3. 使用 /转换 在假名和罗马音之间切换
4. 使用 /admin 密码 题号 查看答案（管理员功能）
5. 使用 /pass 放弃当前题目（每道题只能尝试一次）

注意：
- 每道题只能尝试一次，除非你已经完成了当前题目的所有答案"""
    await help_cmd.finish(help_text)

@dataclass
class GridCell:
    content: str = ""  # 当前填入的内容
    is_filled: bool = False  # 是否需要填写
    question_number: str = ""  # 题号（如果是起始格）

@dataclass
class GameState:
    grid: List[List[GridCell]]  # 游戏网格
    solved_questions: Set[str]  # 已解答的题号
    is_romaji: bool = False  # 是否显示罗马音

# 存储用户当前游戏状态
user_states: Dict[int, GameState] = {}

def create_game_state(question_num: int) -> GameState:
    """创建新的游戏状态"""
    if question_num not in crossword_layouts:
        raise ValueError(f"题目 {question_num} 不存在")
    
    grid_size, _, layout = crossword_layouts[question_num]
    rows, cols = grid_size
    grid = [[GridCell() for _ in range(cols)] for _ in range(rows)]
    
    # 标记需要填写的格子
    for direction, start_coord, length, q_num, _ in layout:
        row = ord(start_coord[0].upper()) - ord('A')
        col = int(start_coord[1:]) - 1
        
        # 设置起始格的题号
        grid[row][col].question_number = q_num
        
        for i in range(length):
            if direction == "横":
                grid[row][col + i].is_filled = True
            else:  # 竖
                grid[row + i][col].is_filled = True
    
    return GameState(grid=grid, solved_questions=set())

def render_game_image(state: GameState) -> Image.Image:
    """将游戏状态渲染为图片"""
    rows = len(state.grid)
    cols = len(state.grid[0])
    
    # 计算图片大小（添加边距）
    width = cols * CELL_SIZE + 2 * PADDING
    height = rows * CELL_SIZE + 2 * PADDING
    
    # 创建图片和绘图对象
    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        romaji_font = ImageFont.truetype(FONT_PATH, ROMAJI_FONT_SIZE)
        small_font = ImageFont.truetype(FONT_PATH, FONT_SIZE // 2)  # 题号使用更小的字体
    except Exception:
        font = ImageFont.load_default()
        romaji_font = font
        small_font = font
    
    # 绘制网格
    for i in range(rows + 1):
        y = PADDING + i * CELL_SIZE
        draw.line([(PADDING, y), (width - PADDING, y)], fill=GRID_COLOR, width=1)
    
    for j in range(cols + 1):
        x = PADDING + j * CELL_SIZE
        draw.line([(x, PADDING), (x, height - PADDING)], fill=GRID_COLOR, width=1)
    
    # 绘制单元格内容
    for i, row in enumerate(state.grid):
        for j, cell in enumerate(row):
            x = PADDING + j * CELL_SIZE
            y = PADDING + i * CELL_SIZE
            
            # 如果不是需要填写的格子，涂成灰色
            if not cell.is_filled:
                draw.rectangle([x + 1, y + 1, x + CELL_SIZE - 1, y + CELL_SIZE - 1], fill="#EEEEEE")
            else:
                if cell.content:
                    # 绘制已填写的答案
                    text = cell.content
                    # 根据状态选择字体
                    current_font = romaji_font if state.is_romaji else font
                    text_bbox = draw.textbbox((0, 0), text, font=current_font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    text_x = x + (CELL_SIZE - text_width) // 2
                    text_y = y + (CELL_SIZE - text_height) // 2
                    draw.text((text_x, text_y), text, fill=TEXT_COLOR, font=current_font)
    
    # 最后绘制题号，确保显示在最上层
    for i, row in enumerate(state.grid):
        for j, cell in enumerate(row):
            if cell.is_filled and cell.question_number:
                x = PADDING + j * CELL_SIZE
                y = PADDING + i * CELL_SIZE
                # 在左上角绘制题号，使用红色
                text_bbox = draw.textbbox((0, 0), cell.question_number, font=small_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = x + 2  # 稍微偏移
                text_y = y + 2
                # 先画一个白色背景，确保题号清晰可见
                draw.rectangle([text_x - 1, text_y - 1, text_x + text_width + 1, text_y + text_height + 1], fill="white")
                draw.text((text_x, text_y), cell.question_number, fill="#FF0000", font=small_font)
    
    return img

def save_game_image(state: GameState, user_id: int) -> str:
    """保存游戏状态图片并返回文件路径"""
    img = render_game_image(state)
    
    # 创建临时目录
    temp_dir = Path(__file__).parent / "temp"
    os.makedirs(str(temp_dir), exist_ok=True)
    
    # 保存图片
    image_path = str(temp_dir / f"game_{user_id}.png")
    img.save(image_path)
    return image_path

@select_cmd.handle()
async def handle_select(event: MessageEvent):
    msg = event.get_plaintext().strip()
    try:
        # 检查消息格式
        if "第" not in msg or "题" not in msg:
            await select_cmd.finish("格式错误，请使用：/选择题目 第X题（支持中文数字）")
            return
            
        parts = msg.split("第")
        if len(parts) != 2:
            await select_cmd.finish("格式错误，请使用：/选择题目 第X题（支持中文数字）")
            return
            
        question_text = parts[1].split("题")[0]
        if not question_text:
            await select_cmd.finish("格式错误，请使用：/选择题目 第X题（支持中文数字）")
            return
            
        try:
            question_num = int(question_text)
        except ValueError:
            question_num = convert_chinese_num(question_text)
        
        # 检查题目是否存在
        if question_num != 3 and question_num not in crossword_layouts:
            await select_cmd.finish(f"题目 {question_num} 不存在")
            return
            
        user_id = event.user_id
        
        # 检查用户是否已经尝试过这道题
        if user_id in user_attempted_questions and question_num in user_attempted_questions[user_id]:
            if question_num == 3:
                await select_cmd.finish(f"你已经尝试过第{question_num}题了，不能重复尝试")
                return
            else:
                # 检查是否所有题目都已答对
                if user_id in user_states:
                    state = user_states[user_id]
                    _, _, layout = crossword_layouts[user_questions[user_id]]
                    all_solved = all(q_num in state.solved_questions for _, _, _, q_num, _ in layout)
                    if not all_solved:
                        await select_cmd.finish(f"你已经尝试过第{question_num}题了，请先完成当前题目或使用 /pass 放弃当前题目")
                        return
                else:
                    await select_cmd.finish(f"你已经尝试过第{question_num}题了，请先完成当前题目或使用 /pass 放弃当前题目")
                    return
        
        user_questions[user_id] = question_num
        
        # 处理第三题
        if question_num == 3:
            question_text = """若一部新作整数作stg（不含花映塚、兽王园）的某面boss在某部新作（含小数点作、花映塚、兽王园）中担任自机，则称该角色为这一面的自机角色。那么，各面自机角色各有几个？

请用逗号分隔的7个数字回答，每个数字代表对应面的自机角色数量。"""
            await select_cmd.finish(Message([
                MessageSegment.text(f"已选择第{question_num}题\n{question_text}\n\n请使用 /作答 1 答案 来提交答案\n答案必须是7个数字，用逗号分隔（支持中文和英文逗号）\n只能提交一次")
            ]))
        else:
            # 处理填字题目
            user_states[user_id] = create_game_state(question_num)
            image_path = save_game_image(user_states[user_id], user_id)
            await select_cmd.finish(Message([
                MessageSegment.text(f"已选择第{question_num}题\n请使用 /作答 题号 答案 来提交答案\n"),
                MessageSegment.image(file=f"file:///{image_path}"),
                MessageSegment.text("请使用 /转换 在假名和罗马音之间切换\n使用 /pass 可以放弃当前题目")
            ]))
    
    except Exception as e:
        pass
        #await select_cmd.finish(f"发生错误：{str(e)}\n请使用：/选择题目 第X题（支持中文数字）")

@answer_cmd.handle()
async def handle_answer(event: MessageEvent):
    user_id = event.user_id
    if user_id not in user_questions:
        await answer_cmd.finish("请先使用 /选择题目 第X题 选择要回答的题目")
        return
    
    grid_num = user_questions[user_id]
    
    # 处理第三题
    if grid_num == 3:
        # 检查是否已经尝试过第三题
        if user_id in user_attempted_questions and 3 in user_attempted_questions[user_id]:
            await answer_cmd.finish("你已经尝试过第三题了，不能再次尝试")
            return
            
        if user_id not in user_states:
            user_states[user_id] = GameState(grid=[], solved_questions=set())
    else:
        # 处理填字题目
        if user_id not in user_states:
            user_states[user_id] = create_game_state(grid_num)
    
    msg = event.get_plaintext().strip()
    parts = msg.split()
    if len(parts) != 3:  # 命令 题号 答案
        await answer_cmd.finish("格式错误，请使用：/作答 题号 答案")
        return
        
    _, question_num, answer = parts
    
    # 验证答案
    is_correct, feedback, display_answer = validate_answer(grid_num, question_num, answer)
    
    if is_correct:
        # 更新游戏状态
        if grid_num == 3:
            # 第三题不需要更新网格状态
            user_states[user_id].solved_questions.add(question_num)
            # 记录用户已尝试过第三题
            if user_id not in user_attempted_questions:
                user_attempted_questions[user_id] = set()
            user_attempted_questions[user_id].add(3)
            # 发送第三题答对图片
            answer3_path = str(PIC_DIR / "answer3.png")
            await answer_cmd.finish(Message([
                MessageSegment.text(feedback),
                MessageSegment.image(file=f"file://{answer3_path}")
            ]))
        else:
            # 更新填字题目的状态
            update_game_state(user_states[user_id], grid_num, question_num, display_answer)
            
            # 检查是否所有题目都答对了
            _, _, layout = crossword_layouts[grid_num]
            all_solved = all(q_num in user_states[user_id].solved_questions for _, _, _, q_num, _ in layout)
            
            if all_solved:
                # 如果全部答对，发送对应题目的答案图片
                answer_path = str(PIC_DIR / f"answer{grid_num}.png")
                await answer_cmd.finish(Message([
                    MessageSegment.text(feedback),
                    MessageSegment.image(file=f"file://{answer_path}")
                ]))
            else:
                # 否则只发送当前状态
                image_path = save_game_image(user_states[user_id], user_id)
                await answer_cmd.finish(Message([
                    MessageSegment.text(f"{feedback}\n当前游戏状态：\n"),
                    MessageSegment.image(file=f"file://{image_path}")
                ]))
    else:
        # 如果第三题答错，记录到已尝试题目中并清除状态
        if grid_num == 3:
            if user_id not in user_attempted_questions:
                user_attempted_questions[user_id] = set()
            user_attempted_questions[user_id].add(3)
            # 清除当前题目状态
            del user_questions[user_id]
            if user_id in user_states:
                del user_states[user_id]
            # 发送第三题答错图片
            error_path = str(PIC_DIR / "error.png")
            await answer_cmd.finish(Message([
                MessageSegment.text("回答错误，请使用 /选择题目 第X题 选择新的题目"),
                MessageSegment.image(file=f"file://{error_path}")
            ]))
        else:
            await answer_cmd.finish(feedback)

def update_game_state(state: GameState, grid_num: int, question_num: str, display_answer: str) -> None:
    """更新游戏状态，使用假名形式显示"""
    # 在布局中查找对应的题目
    _, _, layout = crossword_layouts[grid_num]
    
    # 如果是第二题，需要检查交叉验证
    if grid_num == 2:
        for direction, start_coord, length, q_num, _ in layout:
            if q_num == question_num:
                row = ord(start_coord[0].upper()) - ord('A')
                col = int(start_coord[1:]) - 1
                
                # 检查交叉验证
                for i in range(length):
                    if direction == "横":
                        # 检查上方和下方的交叉
                        if row > 0 and state.grid[row-1][col+i].is_filled and state.grid[row-1][col+i].content:
                            if state.grid[row-1][col+i].content != display_answer[i]:
                                return
                        if row < len(state.grid)-1 and state.grid[row+1][col+i].is_filled and state.grid[row+1][col+i].content:
                            if state.grid[row+1][col+i].content != display_answer[i]:
                                return
                    else:  # 竖
                        # 检查左侧和右侧的交叉
                        if col > 0 and state.grid[row+i][col-1].is_filled and state.grid[row+i][col-1].content:
                            if state.grid[row+i][col-1].content != display_answer[i]:
                                return
                        if col < len(state.grid[0])-1 and state.grid[row+i][col+1].is_filled and state.grid[row+i][col+1].content:
                            if state.grid[row+i][col+1].content != display_answer[i]:
                                return
                
                # 如果通过了交叉验证，填入答案
                for i in range(length):
                    if direction == "横":
                        state.grid[row][col + i].content = display_answer[i]
                    else:  # 竖
                        state.grid[row + i][col].content = display_answer[i]
                
                state.solved_questions.add(question_num)
                return
    
    # 其他题目的处理逻辑保持不变
    for direction, start_coord, length, q_num, _ in layout:
        if q_num == question_num:
            row = ord(start_coord[0].upper()) - ord('A')
            col = int(start_coord[1:]) - 1
            
            # 填入答案（假名形式）
            for i in range(length):
                if direction == "横":
                    state.grid[row][col + i].content = display_answer[i]
                else:  # 竖
                    state.grid[row + i][col].content = display_answer[i]
            
            state.solved_questions.add(question_num)
            return




def render_admin_image(grid_num: int) -> Image.Image:
    """渲染包含所有答案的游戏状态图片"""
    if grid_num not in crossword_layouts:
        raise ValueError(f"题目 {grid_num} 不存在")
    
    grid_size, _, layout = crossword_layouts[grid_num]
    rows, cols = grid_size
    
    # 创建一个临时的游戏状态
    state = GameState(
        grid=[[GridCell() for _ in range(cols)] for _ in range(rows)],
        solved_questions=set()
    )
    
    # 填入所有答案
    for direction, start_coord, length, q_num, answers in layout:
        row = ord(start_coord[0].upper()) - ord('A')
        col = int(start_coord[1:]) - 1
        
        # 设置起始格的题号
        state.grid[row][col].question_number = q_num
        
        # 先标记需要填写的格子
        for i in range(length):
            if direction == "横":
                state.grid[row][col + i].is_filled = True
            else:  # 竖
                state.grid[row + i][col].is_filled = True
        
        # 填入第一个答案（假名形式）
        answer = answers[0]
        if len(answer) != length:
            raise ValueError(f"答案长度不匹配：题目 {q_num} 需要 {length} 个字符，但答案有 {len(answer)} 个字符")
            
        for i in range(length):
            if direction == "横":
                state.grid[row][col + i].content = answer[i]
            else:  # 竖
                state.grid[row + i][col].content = answer[i]
    
    return render_game_image(state)

@admin_cmd.handle()
async def handle_admin(event: MessageEvent):
    msg = event.get_plaintext().strip()
    parts = msg.split()
    
    if len(parts) != 3:  # 命令 密码 题号
        await admin_cmd.finish("格式错误，请使用：/admin 密码 题号")
        return
    
    _, password, grid_num_str = parts
    
    # 验证密码
    if password != PASSWORD:
        await admin_cmd.finish("密码错误")
        return
    
    # 解析题号
    try:
        grid_num = int(grid_num_str)
    except ValueError:
        try:
            grid_num = convert_chinese_num(grid_num_str)
        except:
            await admin_cmd.finish("题号格式错误")
            return
    
    if grid_num not in crossword_layouts:
        await admin_cmd.finish(f"题目 {grid_num} 不存在")
        return
    
    try:
        # 生成答案图片
        img = render_admin_image(grid_num)
        
        # 保存图片
        temp_dir = Path(__file__).parent / "temp"
        os.makedirs(str(temp_dir), exist_ok=True)
        image_path = str(temp_dir / f"admin_game_{grid_num}.png")
        img.save(image_path)
        
        # 发送图片
        await admin_cmd.finish(Message([
            MessageSegment.text(f"第{grid_num}题的答案：\n"),
            MessageSegment.image(file=f"file:///{image_path}")
        ]))
    except ValueError as e:
        await admin_cmd.finish(f"生成答案图片时出错：{str(e)}")
    #except Exception as e:
    #   await admin_cmd.finish(f"生成答案图片时出错：{str(e)}")

def convert_to_romaji(text: str) -> str:
    """将假名转换为罗马音"""
    result = ""
    for char in text:
        result += ROMAJI_MAP.get(char, char)
    return result

@convert_cmd.handle()
async def handle_convert(event: MessageEvent):
    user_id = event.user_id
    if user_id not in user_states:
        await convert_cmd.finish("请先使用 /选择题目 第X题 选择要回答的题目")
        return
    
    state = user_states[user_id]
    grid_num = user_questions[user_id]
    _, is_japanese, _ = crossword_layouts[grid_num]
    
    # 检查是否支持假名转换
    if not is_japanese:
        await convert_cmd.finish("当前题目不支持假名转换功能")
        return
    
    if not state.is_romaji:
        # 转换为罗马音
        for row in state.grid:
            for cell in row:
                if cell.content:
                    cell.content = convert_to_romaji(cell.content)
        state.is_romaji = True
        message = "已将假名转换为罗马音："
    else:
        # 转换回假名
        _, _, layout = crossword_layouts[grid_num]
        for direction, start_coord, length, q_num, answers in layout:
            if q_num in state.solved_questions:
                row = ord(start_coord[0].upper()) - ord('A')
                col = int(start_coord[1:]) - 1
                answer = answers[0]  # 使用假名形式
                for i in range(length):
                    if direction == "横":
                        state.grid[row][col + i].content = answer[i]
                    else:  # 竖
                        state.grid[row + i][col].content = answer[i]
        state.is_romaji = False
        message = "已将罗马音转换回假名："
    
    # 生成并发送新的游戏状态图片
    image_path = save_game_image(state, user_id)
    await convert_cmd.finish(Message([
        MessageSegment.text(f"{message}\n"),
        MessageSegment.image(file=f"file:///{image_path}")
    ]))

# 在全局变量部分添加
user_attempted_questions: Dict[int, Set[int]] = {}  # 记录用户已尝试过的题目

@pass_cmd.handle()
async def handle_pass(event: MessageEvent):
    user_id = event.user_id
    if user_id not in user_questions:
        await pass_cmd.finish("请先使用 /选择题目 第X题 选择要回答的题目")
        return
    
    grid_num = user_questions[user_id]
    
    # 记录用户已尝试过这道题
    if user_id not in user_attempted_questions:
        user_attempted_questions[user_id] = set()
    user_attempted_questions[user_id].add(grid_num)
    
    # 清除当前题目状态
    del user_questions[user_id]
    if user_id in user_states:
        del user_states[user_id]
    
    await pass_cmd.finish(f"已放弃第{grid_num}题\n请使用 /选择题目 第X题 选择新的题目")

@submit_cmd.handle()
async def handle_submit(event: MessageEvent):
    user_id = event.user_id
    if user_id not in user_questions:
        await submit_cmd.finish("请先使用 /选择题目 第X题 选择要回答的题目")
        return
    
    grid_num = user_questions[user_id]
    if grid_num != 2:
        await submit_cmd.finish("只有第二题需要提交答案")
        return
    
    if user_id not in user_states:
        await submit_cmd.finish("请先填写一些答案")
        return
    
    state = user_states[user_id]
    _, _, layout = crossword_layouts[grid_num]
    
    # 检查是否所有题目都已填写
    all_filled = True
    for _, _, _, q_num, _ in layout:
        if q_num not in state.solved_questions:
            all_filled = False
            break
    
    if not all_filled:
        await submit_cmd.finish("请先完成所有题目的填写")
        return
    
    # 进行最终验证
    for _, _, _, q_num, answers in layout:
        # 获取当前填写的答案
        current_answer = ""
        for direction, start_coord, length, q, _ in layout:
            if q == q_num:
                row = ord(start_coord[0].upper()) - ord('A')
                col = int(start_coord[1:]) - 1
                for i in range(length):
                    if direction == "横":
                        current_answer += state.grid[row][col + i].content
                    else:  # 竖
                        current_answer += state.grid[row + i][col].content
                break
        
        # 验证答案是否正确
        if not any(current_answer.lower() == valid_answer.lower() for valid_answer in answers):
            # 如果答案错误，清除所有已填内容
            for row in state.grid:
                for cell in row:
                    cell.content = ""
            state.solved_questions.clear()
            await submit_cmd.finish("答案错误，所有内容已清除，请重新填写")
            return
    
    # 如果全部正确，发送成功消息和图片
    answer_path = str(PIC_DIR / "answer2.png")
    await submit_cmd.finish(Message([
        MessageSegment.text("恭喜你！所有答案都正确！"),
        MessageSegment.image(file=f"file://{answer_path}")
    ]))