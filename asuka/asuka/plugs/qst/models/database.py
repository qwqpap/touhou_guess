import sqlite3
from pathlib import Path
from typing import Dict, Set, Optional

class Database:
    def __init__(self, db_path: str = "qst.db"):
        self.db_path = Path(__file__).parent.parent / db_path
        self.conn = sqlite3.connect(str(self.db_path))
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()
        
        # 用户当前选择的题目
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_questions (
            user_id INTEGER PRIMARY KEY,
            question_num INTEGER NOT NULL
        )
        """)
        
        # 用户已尝试过的题目
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_attempted_questions (
            user_id INTEGER,
            question_num INTEGER,
            PRIMARY KEY (user_id, question_num)
        )
        """)
        
        # 用户游戏状态
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_states (
            user_id INTEGER PRIMARY KEY,
            grid_data TEXT NOT NULL,
            solved_questions TEXT NOT NULL,
            is_romaji INTEGER NOT NULL DEFAULT 0
        )
        """)
        
        self.conn.commit()

    def get_user_question(self, user_id: int) -> Optional[int]:
        """获取用户当前选择的题目"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT question_num FROM user_questions WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

    def set_user_question(self, user_id: int, question_num: int):
        """设置用户当前选择的题目"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO user_questions (user_id, question_num) VALUES (?, ?)",
            (user_id, question_num)
        )
        self.conn.commit()

    def get_attempted_questions(self, user_id: int) -> Set[int]:
        """获取用户已尝试过的题目"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT question_num FROM user_attempted_questions WHERE user_id = ?", (user_id,))
        return {row[0] for row in cursor.fetchall()}

    def add_attempted_question(self, user_id: int, question_num: int):
        """添加用户已尝试过的题目"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO user_attempted_questions (user_id, question_num) VALUES (?, ?)",
            (user_id, question_num)
        )
        self.conn.commit()

    def get_user_state(self, user_id: int) -> Optional[tuple]:
        """获取用户游戏状态"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT grid_data, solved_questions, is_romaji FROM user_states WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result if result else None

    def set_user_state(self, user_id: int, grid_data: str, solved_questions: str, is_romaji: bool):
        """设置用户游戏状态"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO user_states (user_id, grid_data, solved_questions, is_romaji) VALUES (?, ?, ?, ?)",
            (user_id, grid_data, solved_questions, int(is_romaji))
        )
        self.conn.commit()

    def clear_all(self):
        """清空所有数据"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM user_questions")
        cursor.execute("DELETE FROM user_attempted_questions")
        cursor.execute("DELETE FROM user_states")
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        self.conn.close() 