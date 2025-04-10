from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import sys
from typing import Dict, List, Set
from ..models.questions import GridCell, GameState, crossword_layouts
from .. import db

# 设置字体和渲染相关的常量
FONTS_DIR = Path(__file__).parent.parent / "fonts"
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

def render_game_image(state: GameState, user_id: int = None) -> Image.Image:
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
    
    # 最后绘制题号和箭头
    if user_id is not None:
        grid_num = db.get_user_question(user_id)
        if grid_num and grid_num in crossword_layouts:
            _, _, layout = crossword_layouts[grid_num]
            # 遍历所有题目
            for direction, start_coord, length, q_num, _ in layout:
                # 获取起始坐标
                row = ord(start_coord[0].upper()) - ord('A')
                col = int(start_coord[1:]) - 1
                
                x = PADDING + col * CELL_SIZE
                y = PADDING + row * CELL_SIZE
                
                # 绘制题号
                text_bbox = draw.textbbox((0, 0), q_num, font=small_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                if direction == "横":
                    # 横向题目：题号放在左边，箭头向右
                    text_x = x - CELL_SIZE + 2
                    text_y = y + (CELL_SIZE - text_height) // 2
                    # 绘制箭头
                    arrow_y = y + CELL_SIZE - 5
                    draw.line([(x - CELL_SIZE + 5, arrow_y), (x - 5, arrow_y)], fill="#FF0000", width=1)
                    draw.line([(x - 10, arrow_y - 5), (x - 5, arrow_y), (x - 10, arrow_y + 5)], fill="#FF0000", width=1)
                else:
                    # 竖向题目：题号放在上边，箭头向下
                    text_x = x + (CELL_SIZE - text_width) // 2
                    text_y = y - CELL_SIZE + 2
                    # 绘制箭头
                    arrow_x = x + CELL_SIZE - 5
                    draw.line([(arrow_x, y - CELL_SIZE + 5), (arrow_x, y - 5)], fill="#FF0000", width=1)
                    draw.line([(arrow_x - 5, y - 10), (arrow_x, y - 5), (arrow_x + 5, y - 10)], fill="#FF0000", width=1)
                
                # 先画一个白色背景，确保题号清晰可见
                draw.rectangle([text_x - 1, text_y - 1, text_x + text_width + 1, text_y + text_height + 1], fill="white")
                draw.text((text_x, text_y), q_num, fill="#FF0000", font=small_font)
    
    return img

def save_game_image(state: GameState, user_id: int) -> str:
    """保存游戏状态图片并返回文件路径"""
    img = render_game_image(state, user_id)
    
    # 创建临时目录
    temp_dir = Path(__file__).parent.parent / "temp"
    os.makedirs(str(temp_dir), exist_ok=True)
    
    # 保存图片
    image_path = str(temp_dir / f"game_{user_id}.png")
    img.save(image_path)
    return image_path

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
    
    # 创建一个虚拟的user_id来正确判断题目方向
    virtual_user_id = -1
    if virtual_user_id not in user_questions:
        user_questions[virtual_user_id] = grid_num
    
    return render_game_image(state, virtual_user_id) 