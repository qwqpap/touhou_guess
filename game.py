from PIL import Image, ImageDraw

def render_game_image(game_state, is_admin=False):
    """渲染游戏状态为图片"""
    # 创建空白图片
    img = Image.new('RGB', (GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE), 'white')
    draw = ImageDraw.Draw(img)
    
    # 绘制网格
    for i in range(GRID_SIZE + 1):
        # 绘制横线
        draw.line([(0, i * CELL_SIZE), (GRID_SIZE * CELL_SIZE, i * CELL_SIZE)], fill='black')
        # 绘制竖线
        draw.line([(i * CELL_SIZE, 0), (i * CELL_SIZE, GRID_SIZE * CELL_SIZE)], fill='black')
    
    # 绘制已填内容
    for pos, char in game_state['filled'].items():
        x, y = pos
        # 计算文本位置（居中）
        text_bbox = draw.textbbox((0, 0), char, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = x * CELL_SIZE + (CELL_SIZE - text_width) // 2
        text_y = y * CELL_SIZE + (CELL_SIZE - text_height) // 2
        draw.text((text_x, text_y), char, fill='black', font=font)
    
    # 管理员模式下显示坐标
    if is_admin:
        for pos, direction in game_state['coordinates'].items():
            x, y = pos
            coord = game_state['coordinates'][pos]
            # 计算文本位置（左上角）
            text_bbox = draw.textbbox((0, 0), str(coord), font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = x * CELL_SIZE + 2
            text_y = y * CELL_SIZE + 2
            draw.text((text_x, text_y), str(coord), fill='red', font=font)
    
    return img 