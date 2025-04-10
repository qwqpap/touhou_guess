from nonebot import get_driver
from nonebot.plugin import PluginMetadata
from pathlib import Path
import os
import shutil
from .models.database import Database

__plugin_meta__ = PluginMetadata(
    name="填字游戏",
    description="一个基于东方Project的填字游戏插件",
    usage="使用 /help 查看使用说明",
    type="application",
    homepage="https://github.com/your-repo/your-plugin",
    supported_adapters={"~onebot.v11"},
)

driver = get_driver()
db = Database()

@driver.on_startup
async def startup():
    """插件启动时的初始化操作"""
    # 确保必要的目录存在
    # 创建图片目录
    pic_dir = Path(__file__).parent / "pic"
    os.makedirs(str(pic_dir), exist_ok=True)
    
    # 创建临时目录
    temp_dir = Path(__file__).parent / "temp"
    os.makedirs(str(temp_dir), exist_ok=True)
    
    # 创建字体目录
    fonts_dir = Path(__file__).parent / "fonts"
    os.makedirs(str(fonts_dir), exist_ok=True)

@driver.on_shutdown
async def shutdown():
    """插件关闭时的清理操作"""
    # 清理临时文件
    temp_dir = Path(__file__).parent / "temp"
    if temp_dir.exists():
        shutil.rmtree(str(temp_dir))
    # 关闭数据库连接
    db.close()

# 导入命令模块以注册命令
from .commands import commands