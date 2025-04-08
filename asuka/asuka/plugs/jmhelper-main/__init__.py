from pathlib import Path
from typing import Optional, Tuple, Set

import logfire
from nonebot import get_plugin_config, require
from nonebot.plugin import PluginMetadata

logfire.configure(send_to_logfire="if-token-present", scrubbing=False)

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import Alconna, Args, on_alconna, Match
from nonebot.adapters import Bot, Event

import jmcomic
import yaml
from functools import partial
import asyncio
import concurrent.futures
import os

from .config import Config
from .downloader import download_album
from .converter import convert_to_pdf

__plugin_meta__ = PluginMetadata(
    name="JM助手",
    description="下载并转换漫画资源为PDF格式",
    usage="/jm [漫画ID]",
    config=Config,
)

config = get_plugin_config(Config)

# 全局状态控制
is_enabled = True
# 白名单用户ID集合
whitelist: Set[int] = set()

download_command = on_alconna(
    Alconna(
        "jm",
        Args["jmid", str],
    ),
    use_cmd_start=True,
    priority=10,
    block=True,
    aliases={"下载漫画", "下载本子", "JM", "Jm", "jM"},
)

# 添加控制命令
control_command = on_alconna(
    Alconna(
        "停止色色",
    ),
    use_cmd_start=True,
    priority=10,
    block=True,
)

resume_command = on_alconna(
    Alconna(
        "继续色色",
    ),
    use_cmd_start=True,
    priority=10,
    block=True,
)

thread_pool_executor = concurrent.futures.ThreadPoolExecutor()

PLUGIN_DIR = Path(__file__).parent
OPTION_FILE = PLUGIN_DIR / "option.yml"
WHITELIST_FILE = PLUGIN_DIR / "whitelist.yml"

# 读取 jmcomic 配置
option = jmcomic.create_option_by_file(str(OPTION_FILE))

# 读取白名单配置
with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
    whitelist_config = yaml.safe_load(f)
    whitelist = set(whitelist_config.get("whitelist", []))

with open(OPTION_FILE, "r", encoding="utf-8") as f:
    option_dict = yaml.safe_load(f)
    BASE_DIR = Path(option_dict["dir_rule"]["base_dir"]).resolve()


async def process_download(jmid: str) -> Tuple[Optional[Path], Optional[str]]:
    """
    处理下载和转换任务

    Args:
        jmid: 漫画ID

    Returns:
        Tuple[Optional[Path], Optional[str]]: (PDF文件路径, 漫画名称)或错误情况下的(None, None)
    """
    try:
        album_pdf = BASE_DIR / f"{jmid}.pdf"
        if album_pdf.exists():
            logfire.info(f"PDF已存在: {album_pdf}")
            return album_pdf, jmid

        album, _ = await asyncio.get_event_loop().run_in_executor(
            thread_pool_executor, partial(download_album, jmid, option)
        )

        album_name = album.name
        album_dir = BASE_DIR / album_name

        pdf_path = await asyncio.get_event_loop().run_in_executor(
            thread_pool_executor,
            partial(convert_to_pdf, str(album_dir), str(BASE_DIR), jmid),
        )

        return Path(pdf_path), jmid
    except Exception as e:
        logfire.error(f"处理漫画 {jmid} 失败: {str(e)}", exc_info=True)
        return None, None


@download_command.handle()
async def handle_download(bot: Bot, event: Event, jmid: Match[str]):
    global is_enabled
    
    # 检查功能是否启用
    if not is_enabled:
        await download_command.send("功能已暂停，请联系管理员恢复")
        return
        
    # 检查是否在白名单中
    user_id = event.user_id
    
        
    logfire.info(f"收到下载命令，参数：{jmid.result}")
    jmid_value = jmid.result
    await download_command.send(f"正在处理 {jmid_value}，请稍等...")

    try:
        album_pdf, album_name = await process_download(jmid_value)

        if album_pdf and album_name:
            logfire.info(f"准备上传文件：{album_pdf}")
            await bot.upload_group_file(
                group_id=event.group_id,
                file=str(album_pdf),
                name=f"{album_name}.pdf",
                folder="/",
                file_type="application/pdf"
            )
        else:
            await download_command.send(f"处理 {jmid_value} 失败，请检查日志")

    except Exception as e:
        error_message = f"处理 {jmid_value} 时出错: {str(e)}"
        logfire.error(error_message, exc_info=True)
        await download_command.send(error_message)


@control_command.handle()
async def handle_stop(bot: Bot, event: Event):
    global is_enabled
    
    # 检查是否在白名单中
    user_id = event.user_id
    if user_id not in whitelist:
        await control_command.send("抱歉，你没有权限执行此操作")
        return
        
    is_enabled = False
    await control_command.send("已暂停下载功能")


@resume_command.handle()
async def handle_resume(bot: Bot, event: Event):
    global is_enabled
    
    # 检查是否在白名单中
    user_id = event.user_id
    if user_id not in whitelist:
        await resume_command.send("抱歉，你没有权限执行此操作")
        return
        
    is_enabled = True
    await resume_command.send("已恢复下载功能")
