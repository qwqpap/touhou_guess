from typing import Dict, List, Tuple, Set
from dataclasses import dataclass

# 题目布局数据结构
# 格式：{题号: (网格大小, 是否支持假名, [(方向, 内部坐标, 长度, 题号显示, 答案列表), ...])}
crossword_layouts: Dict[int, Tuple[Tuple[int, int], bool, List[Tuple[str, str, int, str, List[str]]]]] = {
    1: (
        (20,20),  # 网格大小 (行数, 列数)
        True,  # 支持假名转换
        [
            ("横", "B1", 5, "1", ["そんびてん", "sonbiten", "孙美天"]),  # 横向用数字1,2,3...
            ("横", "C9", 7, "2", ["こめいじこいし", "komeizikoishi", "komeijikoishi", "古明地恋"]),  
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
        ]
    ),
    2: (
        (26,20),  # 网格大小 (行数, 列数)
        False,  # 不支持假名转换
        [
            ("横", "C3", 8, "1", ["月之妖鸟化猫之幻"]),
            ("横", "F1", 5, "2", ["东方林籁庵"]),
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
            ("横", "A1", 7, "1", ["2,2,6,9,7,7,7"]),  # 数字序列题目
        ]
    )
}

# 题目文本内容
QUESTION_TEXTS = {
    1: {
        "横": {
            "1": "（）（），启动！",
            "2": "喂喂—— 能听到吗——",
            "3": "……氧气是啥来着",
            "4": "主！体！",
            "5": "在诅咒中癫狂的血池地狱啊！ 快快现出真身！",
            "6": "我怎么可能会输给 连核聚变都玩不转的化石人",
            "7": "大紫蛱蝶",
            "8": "她右手拿着笹",
            "9": "事到如今就算是蛇我也要抓来尝尝！",
            "10": "月有丛云 花有风",
            "11": "这（）真啰嗦。\n就在这附近给她剥皮好了。",
            "12": "因为妨碍了宴会的准备\n所以暂且被放逐到了地上\n你不觉得很冤枉吗？"
        },
        "竖": {
            "一": "当怨恨的等级上升时就会发出哔哩哔哩的声音",
            "二": "这就完了？ 真是没骨头的家伙",
            "三": "我还真没拿过什么报酬……休假是什么来着？",
            "四": "Deepseek",
            "五": "凪",
            "六": "制造假币属于犯罪行为",
            "七": "会使用电脑和打印机",
            "八": "零设中和4有关系，但是登场作中4并没有出场",
            "九": "再就是，几乎每天都能保持人类之身这点也算呢！",
            "十": "我也不是只吃霞的。而且食物什么的随地都有的……会有人特地买吗？",
            "十一": "在最后我第一次对你说句实话吧。我所说的话基本上都是谎言，从一开始起哦",
            "十二": "不，那个，我是本人 我不小心迷路了……\n平时都是（）带我 所以没出过问题\n但今天因为赶路…… 有点冒失了"
        }
    },
    2: {
        "横": {
            "1": "莲子和梅莉两人的曲子",
            "2": "在今年4月26日（下下个周六）的北京高校例会名字",
            "3": "一首很吵的原曲",
            "4": "已经去世的一位知名东方画师的社团",
            "5": "这首曲子很好听，但是所在的道中很糟",
            "6": "你可别加减了",
            "7": "一首东方歌曲，以风见幽香的话当标题，却用的守矢神社的曲子，问幽香这句话是什么",
            "8": "HL符卡，被称为香蕉船",
            "9": "布都烧命莲寺首选符卡",
            "10": "没有角色曲的一位角色的一个称号的绿发角色",
            "11": "正邪厨落泪曲",
            "12": "幻听新宝岛",
            "13": "一款东方同人RPG巨作的副标题，该游戏制作组制作完该游戏后因制作它时的内部矛盾而解散"
        },
        "竖": {
            "一": "学术含量最高的东方主题系列同人志",
            "二": "这首曲子参考了永夜的报应",
            "三": "应对精神攻击很强的妖怪类型",
            "四": "橙舞BGM的原曲名",
            "五": "哈、哈、哈、哈、就是、就是、那样、那样！",
            "六": "绵月依姬的称号",
            "七": "去年开众筹的一个社团",
            "八": "紫妈的大招",
            "九": "出典于《开花爷爷》的HL符卡",
            "十": "东方二创游戏中的知名粪作",
            "十一": "像麻将的EN符卡名",
            "十二": "戳啦，极霸猫嘛",
            "十三": "画风争议很大的一位画师",
            "十四": "一位已逝世角色的名"
        }
    },
    3: {
        "横": {
            "1": "若一部新作整数作stg（不含花映塚、兽王园）的某面boss在某部新作（含小数点作、花映塚、兽王园）中担任自机，则称该角色为这一面的自机角色。那么，各面自机角色各有几个？\n\n请用逗号分隔的7个数字回答，每个数字代表对应面的自机角色数量。"
        }
    }
}

# 第三题的答案
NUMBER_SEQUENCE_ANSWER = "2,2,6,9,7,7,7"

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
CHINESE_NUMS = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '千': 1000, '万': 10000
}

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

__all__ = [
    'crossword_layouts',
    'QUESTION_TEXTS',
    'NUMBER_SEQUENCE_ANSWER',
    'DIRECTIONS',
    'CHINESE_NUMS',
    'GridCell',
    'GameState'
] 