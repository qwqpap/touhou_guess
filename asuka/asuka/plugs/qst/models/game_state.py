from typing import Dict, List, Set
from .questions import GridCell, GameState, crossword_layouts

# 存储用户当前选择的题目
user_questions: Dict[int, int] = {}

# 存储用户当前游戏状态
user_states: Dict[int, GameState] = {}

# 记录用户已尝试过的题目
user_attempted_questions: Dict[int, Set[int]] = {}

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

def update_game_state(state: GameState, grid_num: int, question_num: str, display_answer: str) -> None:
    """更新游戏状态，根据当前显示模式使用假名或罗马音"""
    # 处理第三题
    if grid_num == 3:
        # 第三题不需要更新网格，只需要添加到已解答集合
        state.solved_questions.add(question_num)
        return
    
    # 在布局中查找对应的题目
    _, _, layout = crossword_layouts[grid_num]
    
    # 如果是第二题，需要检查交叉验证
    if grid_num == 2:
        for direction, start_coord, length, q_num, _ in layout:
            if q_num == question_num:
                row = ord(start_coord[0].upper()) - ord('A')
                col = int(start_coord[1:]) - 1
                
                # 填入答案
                for i in range(length):
                    if direction == "横":
                        state.grid[row][col + i].content = display_answer[i]
                    else:  # 竖
                        state.grid[row + i][col].content = display_answer[i]
                
                # 添加到已解答集合
                state.solved_questions.add(question_num)
                return
    
    # 其他题目的处理逻辑
    for direction, start_coord, length, q_num, answers in layout:
        if q_num == question_num:
            row = ord(start_coord[0].upper()) - ord('A')
            col = int(start_coord[1:]) - 1
            
            # 获取假名答案
            kana_answer = answers[0]  # 假名答案在第一个位置
            
            # 根据当前显示模式选择答案形式
            if state.is_romaji:
                # 如果是罗马音模式，将每个假名转换为对应的罗马音
                romaji_map = {
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
                # 将每个假名转换为对应的罗马音
                romaji_answer = [romaji_map.get(kana, kana) for kana in kana_answer]
                answer = romaji_answer
            else:
                # 如果是假名模式，直接使用假名
                answer = kana_answer
            
            # 填入答案
            for i in range(length):
                if direction == "横":
                    state.grid[row][col + i].content = answer[i]
                else:  # 竖
                    state.grid[row + i][col].content = answer[i]
            
            state.solved_questions.add(question_num)
            return

__all__ = [
    'user_questions',
    'user_states',
    'user_attempted_questions',
    'create_game_state',
    'update_game_state'
] 