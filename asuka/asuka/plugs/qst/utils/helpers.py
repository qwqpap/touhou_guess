from typing import Dict, List, Tuple, Set
from ..models.questions import CHINESE_NUMS, crossword_layouts, NUMBER_SEQUENCE_ANSWER

def convert_chinese_num(chinese_str: str) -> int:
    """将中文数字转换为阿拉伯数字"""
    result = 0
    temp = 0
    for char in chinese_str:
        if char in CHINESE_NUMS:
            if CHINESE_NUMS[char] >= 10:
                if temp == 0:
                    temp = 1
                result += temp * CHINESE_NUMS[char]
                temp = 0
            else:
                temp = CHINESE_NUMS[char]
    if temp:
        result += temp
    return result

def convert_to_romaji(kana: str) -> str:
    """将假名转换为罗马音"""
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
    return ''.join(romaji_map.get(char, char) for char in kana)

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
            # 如果是第二题，只检查长度
            if grid_num == 2:
                if len(answer) != length:
                    return False, f"答案长度错误，需要{length}个字符", ""
                return True, "答案已填入，请继续完成其他题目或使用 /提交 提交答案", answer
            
            # 其他题目先验证答案
            if any(answer.lower() == valid_answer.lower() for valid_answer in answers):
                # 验证通过后再检查长度
                if len(answers[0]) != length:
                    return False, f"答案长度错误，需要{length}个字符", ""
                return True, "回答正确！", answers[0]  # 返回假名形式
            return False, "回答错误，请重试", ""
    
    return False, f"题号 {question_num} 不存在", "" 