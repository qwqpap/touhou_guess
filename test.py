import sys
import json
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                            QPushButton, QCheckBox, QMessageBox, QFrame)
from PyQt6.QtGui import QPainter, QPen, QFont
from PyQt6.QtCore import Qt, QRect
from PIL import Image, ImageDraw, ImageFont

class CrosswordCanvas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = (15, 15)
        self.grid = {}
        self.cell_size = 30
        self.setMinimumSize(400, 300)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.setStyleSheet("background-color: white;")

    def set_grid_size(self, rows, cols):
        self.grid_size = (rows, cols)
        self.update()

    def set_grid(self, grid):
        self.grid = grid
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算起始位置，使网格居中
        start_x = int((self.width() - self.grid_size[1] * self.cell_size) / 2)
        start_y = int((self.height() - self.grid_size[0] * self.cell_size) / 2)

        # 绘制网格
        for r in range(self.grid_size[0]):
            for c in range(self.grid_size[1]):
                x = start_x + c * self.cell_size
                y = start_y + r * self.cell_size
                
                # 绘制单元格
                painter.setPen(QPen(Qt.GlobalColor.gray))
                painter.drawRect(QRect(x, y, self.cell_size, self.cell_size))
                
                # 填写内容
                if (r, c) in self.grid:
                    painter.setFont(QFont("Arial", 12))
                    painter.drawText(QRect(x, y, self.cell_size, self.cell_size),
                                   Qt.AlignmentFlag.AlignCenter,
                                   self.grid[(r, c)])

        # 绘制坐标标签
        painter.setFont(QFont("Arial", 10))
        for c in range(self.grid_size[1]):
            x = start_x + c * self.cell_size + self.cell_size // 2
            painter.drawText(x, start_y - 20, chr(c + ord('A')))

        for r in range(self.grid_size[0]):
            y = start_y + r * self.cell_size + self.cell_size // 2
            painter.drawText(start_x - 30, y, str(r + 1))

class CrosswordGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.grid = {}
        self.problems = []
        self.grid_size = (15, 15)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('东方填字游戏生成器')
        self.setMinimumSize(800, 600)

        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # 左侧控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)

        # 网格大小设置
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("网格大小"))
        self.rows_edit = QLineEdit("15")
        self.cols_edit = QLineEdit("15")
        self.rows_edit.setFixedWidth(50)
        self.cols_edit.setFixedWidth(50)
        size_layout.addWidget(self.rows_edit)
        size_layout.addWidget(QLabel("×"))
        size_layout.addWidget(self.cols_edit)
        control_layout.addLayout(size_layout)

        # 连接网格大小改变信号
        self.rows_edit.textChanged.connect(self.on_grid_size_changed)
        self.cols_edit.textChanged.connect(self.on_grid_size_changed)

        # 是否支持假名转换
        self.is_japanese_check = QCheckBox("支持假名转换")
        self.is_japanese_check.setChecked(True)
        control_layout.addWidget(self.is_japanese_check)

        # 输入区域
        self.kanji_edit = QLineEdit()
        self.kana_edit = QLineEdit()
        self.roma_edit = QLineEdit()
        self.position_edit = QLineEdit()
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["横", "竖"])

        control_layout.addWidget(QLabel("汉字（例：犬走椛）"))
        control_layout.addWidget(self.kanji_edit)
        control_layout.addWidget(QLabel("假名（例：いぬばしりもみじ）"))
        control_layout.addWidget(self.kana_edit)
        control_layout.addWidget(QLabel("罗马音（例：inubashirimomiji）"))
        control_layout.addWidget(self.roma_edit)
        control_layout.addWidget(QLabel("起始坐标（例：A2）"))
        control_layout.addWidget(self.position_edit)
        control_layout.addWidget(QLabel("方向"))
        control_layout.addWidget(self.direction_combo)

        # 控制按钮
        add_button = QPushButton("添加词语")
        add_button.setStyleSheet("background-color: #4CAF50; color: white;")
        add_button.clicked.connect(self.add_entry)
        generate_button = QPushButton("生成填字游戏")
        generate_button.setStyleSheet("background-color: #2196F3; color: white;")
        generate_button.clicked.connect(self.generate)

        control_layout.addWidget(add_button)
        control_layout.addWidget(generate_button)
        control_layout.addStretch()

        # 右侧预览画布
        self.canvas = CrosswordCanvas()
        self.canvas.set_grid_size(self.grid_size[0], self.grid_size[1])

        # 添加到主布局
        layout.addWidget(control_panel, 1)
        layout.addWidget(self.canvas, 2)

    def on_grid_size_changed(self):
        """处理网格大小改变"""
        try:
            rows = int(self.rows_edit.text())
            cols = int(self.cols_edit.text())
            if rows > 0 and cols > 0:
                self.grid_size = (rows, cols)
                self.canvas.set_grid_size(rows, cols)
                # 清空网格数据
                self.grid = {}
                self.problems = []
        except ValueError:
            pass  # 忽略非数字输入

    def parse_kana(self, kana: str) -> str:
        """解析假名字符串"""
        kana = re.sub(r'\s+', '', kana)
        if not kana:
            raise ValueError("假名不能为空")
        return kana

    def parse_position(self, pos: str) -> tuple:
        """解析坐标（如A2 → (0,1)）"""
        try:
            col = ord(pos[0].upper()) - ord('A')
            row = int(pos[1:]) - 1
            return (row, col)
        except:
            raise ValueError("坐标格式错误，示例：A2")

    def add_entry(self):
        try:
            # 获取输入
            kana = self.parse_kana(self.kana_edit.text())
            row, col = self.parse_position(self.position_edit.text())
            direction = self.direction_combo.currentText()

            # 确定方向向量
            dr = 0 if direction == "横" else 1
            dc = 1 if direction == "横" else 0

            # 检查是否超出网格范围
            if row < 0 or row >= self.grid_size[0] or col < 0 or col >= self.grid_size[1]:
                raise ValueError("坐标超出网格范围")

            # 检查冲突
            path = []
            for i, char in enumerate(kana):
                r = row + dr * i
                c = col + dc * i
                if r >= self.grid_size[0] or c >= self.grid_size[1]:
                    raise ValueError("词语超出网格范围")
                pos = (r, c)

                if pos in self.grid:
                    if self.grid[pos] != char:
                        raise ValueError(f"位置冲突：{pos} 已存在 {self.grid[pos]}")
                path.append(pos)

            # 更新网格
            for pos, char in zip(path, kana):
                self.grid[pos] = char

            # 保存记录
            self.problems.append({
                "kanji": self.kanji_edit.text(),
                "kana": kana,
                "roma": self.roma_edit.text(),
                "position": self.position_edit.text().upper(),
                "direction": direction,
                "path": [(r + 1, c) for r, c in path]  # 转换为1-based坐标
            })

            # 清空输入
            self.kanji_edit.clear()
            self.kana_edit.clear()
            self.roma_edit.clear()
            self.position_edit.clear()

            # 更新预览
            self.canvas.set_grid(self.grid)
            QMessageBox.information(self, "成功", "已添加词语并更新预览！")

        except Exception as e:
            QMessageBox.critical(self, "输入错误", str(e))

    def generate(self):
        """生成最终结果"""
        try:
            # 更新网格大小
            self.grid_size = (int(self.rows_edit.text()), int(self.cols_edit.text()))
            self.canvas.set_grid_size(self.grid_size[0], self.grid_size[1])
            
            # 创建题目数据
            crossword_data = {
                "grid_size": self.grid_size,
                "is_japanese": self.is_japanese_check.isChecked(),
                "problems": []
            }
            
            # 添加所有问题
            for problem in self.problems:
                direction, start_coord = problem["direction"], problem["position"]
                length = len(problem["kana"])
                q_num = str(len(crossword_data["problems"]) + 1)
                if direction == "竖":
                    q_num = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][len(crossword_data["problems"])]
                
                crossword_data["problems"].append([
                    direction,
                    start_coord,
                    length,
                    q_num,
                    [problem["kana"], problem["roma"], problem["kanji"]]
                ])
            
            # 保存数据
            with open("crossword_data.json", "w", encoding='utf-8') as f:
                json.dump(crossword_data, f, ensure_ascii=False, indent=2)
            
            # 生成预览图片
            img = Image.new('RGB', (800, 600), 'white')
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("msgothic.ttc", 20)
            
            # 绘制设置
            cell_size = 40
            start_x, start_y = 100, 100
            
            # 绘制网格
            for r in range(self.grid_size[0]):
                for c in range(self.grid_size[1]):
                    x = start_x + c * cell_size
                    y = start_y + r * cell_size
                    
                    draw.rectangle([x, y, x + cell_size, y + cell_size],
                                 outline='black')
                    
                    if (r, c) in self.grid:
                        draw.text((x + 10, y + 5), self.grid[(r, c)],
                                font=font, fill='black')
            
            # 保存图片
            img.save("crossword.png")
            
            QMessageBox.information(self, "完成", "生成成功！\ncrossword.png\ncrossword_data.json")
            
        except Exception as e:
            QMessageBox.critical(self, "生成错误", str(e))

def main():
    app = QApplication(sys.argv)
    window = CrosswordGenerator()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()