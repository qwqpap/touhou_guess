import tkinter as tk
from tkinter import messagebox
import random
from typing import List, Optional, Tuple
import json
import os

class WordleGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Wordle 游戏")
        self.root.geometry("800x600")
        
        # 游戏配置
        self.WORD_LENGTH = 5
        self.MAX_ATTEMPTS = 6
        self.COLORS = {
            'correct': '#538d4e',    # 绿色
            'present': '#b59f3b',    # 黄色
            'absent': '#3a3a3c',     # 灰色
            'default': '#121213',    # 默认背景色
            'text': '#ffffff'        # 文字颜色
        }
        
        # 游戏状态
        self.current_attempt = 0
        self.current_word = ""
        self.target_word = ""
        self.game_over = False
        
        # 加载单词列表
        self.words = self._load_words()
        
        # 初始化UI
        self._init_ui()
        
        # 绑定键盘事件
        self._bind_events()
        
        # 开始新游戏
        self.new_game()

    def _load_words(self) -> List[str]:
        """加载单词列表"""
        try:
            with open('words.txt', 'r', encoding='utf-8') as f:
                return [word.strip().upper() for word in f.readlines()]
        except FileNotFoundError:
            messagebox.showerror("错误", "找不到单词文件 words.txt")
            return []

    def _init_ui(self) -> None:
        """初始化游戏界面"""
        # 创建主框架
        self.main_frame = tk.Frame(self.root, bg=self.COLORS['default'])
        self.main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # 创建标题
        title_label = tk.Label(
            self.main_frame,
            text="WORDLE",
            font=('Arial', 32, 'bold'),
            bg=self.COLORS['default'],
            fg=self.COLORS['text']
        )
        title_label.pack(pady=(0, 20))
        
        # 创建游戏网格
        self.grid_frame = tk.Frame(self.main_frame, bg=self.COLORS['default'])
        self.grid_frame.pack(pady=20)
        
        # 创建字母网格
        self.letter_labels = []
        for i in range(self.MAX_ATTEMPTS):
            row = []
            for j in range(self.WORD_LENGTH):
                label = tk.Label(
                    self.grid_frame,
                    text="",
                    width=2,
                    height=1,
                    font=('Arial', 24, 'bold'),
                    bg=self.COLORS['default'],
                    fg=self.COLORS['text'],
                    relief='solid',
                    borderwidth=2
                )
                label.grid(row=i, column=j, padx=2, pady=2)
                row.append(label)
            self.letter_labels.append(row)
        
        # 创建键盘
        self._create_keyboard()
        
        # 创建新游戏按钮
        self.new_game_button = tk.Button(
            self.main_frame,
            text="新游戏",
            command=self.new_game,
            font=('Arial', 12),
            bg=self.COLORS['default'],
            fg=self.COLORS['text']
        )
        self.new_game_button.pack(pady=20)

    def _create_keyboard(self) -> None:
        """创建虚拟键盘"""
        self.keyboard_frame = tk.Frame(self.main_frame, bg=self.COLORS['default'])
        self.keyboard_frame.pack(pady=20)
        
        # 键盘布局
        keyboard_layout = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['ENTER', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'BACKSPACE']
        ]
        
        self.key_buttons = {}
        for i, row in enumerate(keyboard_layout):
            for j, key in enumerate(row):
                width = 4 if key in ['ENTER', 'BACKSPACE'] else 2
                btn = tk.Button(
                    self.keyboard_frame,
                    text=key,
                    width=width,
                    command=lambda k=key: self._handle_key_press(k),
                    font=('Arial', 10),
                    bg=self.COLORS['default'],
                    fg=self.COLORS['text']
                )
                btn.grid(row=i, column=j, padx=1, pady=1)
                self.key_buttons[key] = btn

    def _bind_events(self) -> None:
        """绑定键盘事件"""
        self.root.bind('<Key>', lambda e: self._handle_key_press(e.char.upper()))
        self.root.bind('<BackSpace>', lambda e: self._handle_key_press('BACKSPACE'))
        self.root.bind('<Return>', lambda e: self._handle_key_press('ENTER'))

    def new_game(self) -> None:
        """开始新游戏"""
        self.current_attempt = 0
        self.current_word = ""
        self.game_over = False
        self.target_word = random.choice(self.words)
        
        # 重置界面
        for row in self.letter_labels:
            for label in row:
                label.config(text="", bg=self.COLORS['default'])
        
        for btn in self.key_buttons.values():
            btn.config(bg=self.COLORS['default'])

    def _handle_key_press(self, key: str) -> None:
        """处理按键事件"""
        if self.game_over:
            return
            
        if key == 'ENTER':
            self._check_word()
        elif key == 'BACKSPACE':
            self._handle_backspace()
        elif key in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            self._handle_letter(key)

    def _handle_letter(self, letter: str) -> None:
        """处理字母输入"""
        if len(self.current_word) < self.WORD_LENGTH:
            self.current_word += letter
            self.letter_labels[self.current_attempt][len(self.current_word) - 1].config(text=letter)

    def _handle_backspace(self) -> None:
        """处理退格键"""
        if self.current_word:
            self.current_word = self.current_word[:-1]
            self.letter_labels[self.current_attempt][len(self.current_word)].config(text="")

    def _check_word(self) -> None:
        """检查当前单词"""
        if len(self.current_word) != self.WORD_LENGTH:
            messagebox.showwarning("提示", "请输入5个字母的单词！")
            return
            
        if self.current_word not in self.words:
            messagebox.showwarning("提示", "这不是一个有效的单词！")
            return
            
        # 检查每个字母
        for i, letter in enumerate(self.current_word):
            label = self.letter_labels[self.current_attempt][i]
            if letter == self.target_word[i]:
                label.config(bg=self.COLORS['correct'])
                self.key_buttons[letter].config(bg=self.COLORS['correct'])
            elif letter in self.target_word:
                label.config(bg=self.COLORS['present'])
                if self.key_buttons[letter].cget('bg') != self.COLORS['correct']:
                    self.key_buttons[letter].config(bg=self.COLORS['present'])
            else:
                label.config(bg=self.COLORS['absent'])
                if self.key_buttons[letter].cget('bg') not in [self.COLORS['correct'], self.COLORS['present']]:
                    self.key_buttons[letter].config(bg=self.COLORS['absent'])
        
        # 检查是否获胜
        if self.current_word == self.target_word:
            self.game_over = True
            messagebox.showinfo("恭喜", "你赢了！")
            return
            
        # 检查是否失败
        self.current_attempt += 1
        if self.current_attempt >= self.MAX_ATTEMPTS:
            self.game_over = True
            messagebox.showinfo("游戏结束", f"正确答案是: {self.target_word}")

if __name__ == "__main__":
    root = tk.Tk()
    game = WordleGame(root)
    root.mainloop() 