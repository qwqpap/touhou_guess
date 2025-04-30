from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from ..models.questions import (
    QUESTION_TEXTS,
    crossword_layouts,
    NUMBER_SEQUENCE_ANSWER,
    DIRECTIONS,
    CHINESE_NUMS,
    GridCell,
    GameState
)
from ..models.game_state import create_game_state, update_game_state
from ..utils.helpers import convert_chinese_num, validate_answer, convert_to_romaji
from ..utils.render import save_game_image, render_game_image, render_admin_image
from pathlib import Path
import os
import json
from .. import db

PIC_DIR = Path(__file__).parent.parent / "pic"
PASSWORD = "saitama2000"

# 命令注册
help_cmd = on_command("help", priority=10, block=True)
select_cmd = on_command("选择题目", priority=10, block=True, aliases={"x"})
answer_cmd = on_command("作答", priority=10, block=True, aliases={"z"})
admin_cmd = on_command("admin", priority=10, block=True, aliases={"ad"})
convert_cmd = on_command("转换", priority=10, block=True, aliases={"sw"})
pass_cmd = on_command("pass", priority=10, block=True, aliases={"p"})
submit_cmd = on_command("提交", priority=10, block=True, aliases={"t"})
query_cmd = on_command("查询", priority=10, block=True, aliases={"c"})
erase_cmd = on_command("擦除", priority=10, block=True, aliases={"d"})

@help_cmd.handle()
async def handle_help():
    help_text = """填字游戏使用说明：
1. 使用 /选择题目 或者/x 第X题 来选择要回答的题目（支持中文数字，如：第一题）
2. 使用 /作答 或者/z 题号 答案 来提交答案
   - 横向题目用数字表示：1, 2, 3...
   - 竖向题目用中文数字表示：一, 二, 三...
3. 使用 /转换 或者/sw 在假名和罗马音之间切换
4. 使用 /admin 或者/ad 密码 题号 查看答案（管理员功能）
5. 使用 /pass 或者/p 放弃当前题目（每道题只能尝试一次）

注意：
- 每道题只能尝试一次，除非你已经完成了当前题目的所有答案"""
    await help_cmd.finish(help_text)

@query_cmd.handle()
async def handle_query(event: MessageEvent):
    msg = event.get_plaintext().strip()
    
    # 检查消息格式
    if len(msg.split()) != 2:  # 命令 题号
        return await query_cmd.send("格式错误，请使用：/查询 或者/c 题号（支持中文数字）")
        
    _, question_num = msg.split()
    
    # 检查用户是否选择了题目
    user_id = event.user_id
    grid_num = db.get_user_question(user_id)
    if not grid_num:
        return await query_cmd.send("请先使用 /选择题目 或者/x 第X题 选择要回答的题目")
    
    if grid_num not in QUESTION_TEXTS:
        return await query_cmd.send("当前题目没有文本内容")
    
    # 检查题号格式
    is_chinese = False
    try:
        # 尝试转换为数字
        num = int(question_num)
    except ValueError:
        # 如果是中文数字，转换为阿拉伯数字
        try:
            num = convert_chinese_num(question_num)
            is_chinese = True
        except:
            return await query_cmd.send("题号格式错误，请使用阿拉伯数字或中文数字")
    
    # 根据题号格式选择方向
    direction = "竖" if is_chinese else "横"
    question_num_str = question_num if is_chinese else str(num)
    
    # 获取题目内容
    if direction in QUESTION_TEXTS[grid_num] and question_num_str in QUESTION_TEXTS[grid_num][direction]:
        content = QUESTION_TEXTS[grid_num][direction][question_num_str]
        return await query_cmd.send(f"第{grid_num}题 {direction}向第{question_num}题：\n{content}")
    else:
        return await query_cmd.send(f"未找到第{grid_num}题 {direction}向第{question_num}题的内容")

@select_cmd.handle()
async def handle_select(event: MessageEvent):
    msg = event.get_plaintext().strip()
    try:
        # 检查消息格式
        if "第" not in msg or "题" not in msg:
            await select_cmd.finish("格式错误，请使用：/选择题目 或者/x 第X题（支持中文数字）")
            return
            
        parts = msg.split("第")
        if len(parts) != 2:
            await select_cmd.finish("格式错误，请使用：/选择题目 或者/x 第X题（支持中文数字）")
            return
            
        question_text = parts[1].split("题")[0]
        if not question_text:
            await select_cmd.finish("格式错误，请使用：/选择题目 或者/x 第X题（支持中文数字）")
            return
            
        try:
            question_num = int(question_text)
        except ValueError:
            question_num = convert_chinese_num(question_text)
        
        # 检查题目是否存在
        if question_num != 3 and question_num not in crossword_layouts:
            await select_cmd.finish(f"题目 {question_num} 不存在")
            return
            
        user_id = event.user_id
        
        # 检查用户是否已经尝试过这道题
        attempted_questions = db.get_attempted_questions(user_id)
        if question_num in attempted_questions:
            if question_num == 3:
                await select_cmd.finish(f"你已经尝试过第{question_num}题了，不能重复尝试")
                return
            else:
                # 检查是否所有题目都已答对
                state = db.get_user_state(user_id)
                if state:
                    grid_data, solved_questions, _ = state
                    solved_questions = set(json.loads(solved_questions))
                    _, _, layout = crossword_layouts[question_num]
                    all_solved = all(q_num in solved_questions for _, _, _, q_num, _ in layout)
                    if all_solved:
                        await select_cmd.finish(f"你已经完成第{question_num}题了，请选择其他题目")
                        return
                    else:
                        # 检查用户当前是否有正在进行的题目
                        current_question = db.get_user_question(user_id)
                        if current_question and current_question != question_num:
                            await select_cmd.finish(f"你已经尝试过第{question_num}题了，请先完成当前题目或使用 /pass 放弃当前题目")
                            return
                        # 如果用户当前没有正在进行的题目，允许重新选择
                        pass
        
        db.set_user_question(user_id, question_num)
        
        # 处理第三题
        if question_num == 3:
            question_text = """若一部新作整数作stg（不含花映塚、兽王园）的某面boss在某部新作（含小数点作、花映塚、兽王园）中担任自机，则称该角色为这一面的自机角色。那么，各面自机角色各有几个？

请用逗号分隔的7个数字回答，每个数字代表对应面的自机角色数量。注：只有关底Boss算该面Boss，多个关底Boss则分开计算。以旧作为例，雪、舞都是怪绮谈四面Boss，所以她们是分开计算的"""
            await select_cmd.finish(Message([
                MessageSegment.text(f"已选择第{question_num}题\n{question_text}\n\n请使用 /作答 1 答案 来提交答案\n答案必须是7个数字，用逗号分隔（支持中文和英文逗号）\n只能提交一次")
            ]))
            return
        else:
            # 处理填字题目
            game_state = create_game_state(question_num)
            db.set_user_state(
                user_id,
                json.dumps([[cell.__dict__ for cell in row] for row in game_state.grid]),
                json.dumps(list(game_state.solved_questions)),
                game_state.is_romaji
            )
            image_path = save_game_image(game_state, user_id)
            if question_num == 2:
                await select_cmd.send(f"已选择第{question_num}题\n请使用 /作答 或者/z 题号 答案 来提交答案\n使用 /擦除 题号 可以擦除已填写的答案\n使用 /转换 或者/sw 在假名和罗马音之间切换\n使用 /pass 或者/p 可以放弃当前题目\n使用 /查询 或者/c 题号 可以查询题目内容\n")
                await select_cmd.finish(Message([
                    MessageSegment.image(f"file:///{image_path}")
                ]))
                return
            else:
                await select_cmd.send(f"已选择第{question_num}题\n请使用 /作答 或者/z 题号 答案 来提交答案\n使用 /擦除 或者/d 题号 可以擦除已填写的答案\n使用 /转换 或者/sw 在假名和罗马音之间切换\n使用 /pass 或者/p 可以放弃当前题目\n使用 /查询 或者/c 题号 可以查询题目内容，翻译以thbwiki为准\n")
                await select_cmd.finish(Message([
                    MessageSegment.image(f"file:///{image_path}"),
                    MessageSegment.text("\n请使用 /转换 或者/sw 在假名和罗马音之间切换\n使用 /pass 或者/p 可以放弃当前题目")
                ]))
                return
    
    except Exception as e:
        if "FinishedException" not in str(e):
            await select_cmd.finish("发生错误，请稍后重试")

@answer_cmd.handle()
async def handle_answer(event: MessageEvent):
    user_id = event.user_id
    grid_num = db.get_user_question(user_id)
    if not grid_num:
        await answer_cmd.finish("请先使用 /选择题目 或者/x 第X题 选择要回答的题目")
        return
    
    # 处理第三题
    if grid_num == 3:
        # 检查是否已经尝试过第三题
        attempted_questions = db.get_attempted_questions(user_id)
        if 3 in attempted_questions:
            await answer_cmd.finish("你已经尝试过第三题了，不能再次尝试")
            return
            
        state = db.get_user_state(user_id)
        if not state:
            db.set_user_state(user_id, "[]", "[]", False)
    else:
        # 处理填字题目
        state = db.get_user_state(user_id)
        if not state:
            game_state = create_game_state(grid_num)
            db.set_user_state(
                user_id,
                json.dumps([[cell.__dict__ for cell in row] for row in game_state.grid]),
                json.dumps(list(game_state.solved_questions)),
                game_state.is_romaji
            )
    
    msg = event.get_plaintext().strip()
    parts = msg.split()
    if len(parts) != 3:  # 命令 题号 答案
        await answer_cmd.finish("格式错误，请使用：/作答 或者/z 题号 答案")
        return
        
    _, question_num, answer = parts
    
    # 验证答案
    is_correct, feedback, display_answer = validate_answer(grid_num, question_num, answer)
    
    if is_correct:
        # 更新游戏状态
        state = db.get_user_state(user_id)
        if state:
            grid_data, solved_questions, is_romaji = state
            grid_data = json.loads(grid_data)
            solved_questions = set(json.loads(solved_questions))
            
            # 创建游戏状态对象
            game_state = GameState(
                grid=[[GridCell(**cell) for cell in row] for row in grid_data],
                solved_questions=solved_questions,
                is_romaji=bool(is_romaji)
            )
            
            # 更新状态
            update_game_state(game_state, grid_num, question_num, display_answer)
            
            # 保存更新后的状态
            db.set_user_state(
                user_id,
                json.dumps([[cell.__dict__ for cell in row] for row in game_state.grid]),
                json.dumps(list(game_state.solved_questions)),
                game_state.is_romaji
            )
            
            # 添加到已尝试题目
            db.add_attempted_question(user_id, grid_num)
            
            # 检查是否所有题目都已答对
            _, _, layout = crossword_layouts[grid_num]
            all_solved = all(q_num in game_state.solved_questions for _, _, _, q_num, _ in layout)
            
            if all_solved:
                # 如果是第二题，发送答案图片
                if grid_num == 2:
                    answer_path = str(PIC_DIR / f"answer{grid_num}.png")
                    # 清除当前题目状态
                    db.set_user_question(user_id, 0)
                    db.set_user_state(user_id, "[]", "[]", False)
                    await answer_cmd.finish(Message([
                        MessageSegment.text("恭喜你完成所有题目！\n"),
                        MessageSegment.image(f"file:///{answer_path}"),
                        MessageSegment.text("\n请使用 /选择题目 第X题 选择新的题目")
                    ]))
                else:
                    # 其他题目显示答案图片
                    answer_path = str(PIC_DIR / f"answer{grid_num}.png")
                    # 清除当前题目状态
                    db.set_user_question(user_id, 0)
                    db.set_user_state(user_id, "[]", "[]", False)
                    await answer_cmd.finish(Message([
                        MessageSegment.text(f"{feedback}\n所有题目已填写完成，请使用 /提交 提交答案\n当前游戏状态：\n"),
                        MessageSegment.image(f"file:///{answer_path}"),
                        MessageSegment.text("\n请使用 /选择题目 第X题 选择新的题目")
                    ]))
            else:
                # 生成并发送图片
                image_path = save_game_image(game_state, user_id)
                await answer_cmd.finish(Message([
                    MessageSegment.text(feedback + "\n"),
                    MessageSegment.image(f"file:///{image_path}")
                ]))
        else:
            await answer_cmd.finish("游戏状态错误，请重新选择题目")
    else:
        await answer_cmd.finish(feedback)

@admin_cmd.handle()
async def handle_admin(event: MessageEvent):
    msg = event.get_plaintext().strip()
    parts = msg.split()
    
    if len(parts) < 2:
        await admin_cmd.finish("格式错误，请使用：/admin 密码 [命令] [参数]\n可用命令：\n- clear: 清除所有用户的答题记录\n- answer 题号: 查看指定题目的答案")
        return
    
    password = parts[1]
    if password != PASSWORD:
        await admin_cmd.finish("密码错误")
        return
    
    if len(parts) == 2:
        # 显示帮助信息
        await admin_cmd.finish("格式错误，请使用：/admin 密码 [命令] [参数]\n可用命令：\n- clear: 清除所有用户的答题记录\n- answer 题号: 查看指定题目的答案")
        return
    
    command = parts[2]
    if command == "clear":
        # 清除所有用户的答题记录
        db.clear_all_data()
        await admin_cmd.finish("已清除所有用户的答题记录")
        return
    elif command == "answer":
        if len(parts) != 4:
            await admin_cmd.finish("格式错误，请使用：/admin 密码 answer 题号")
            return
        
        try:
            question_num = int(parts[3])
        except ValueError:
            await admin_cmd.finish("题号必须是数字")
            return
        
        if question_num not in crossword_layouts:
            await admin_cmd.finish(f"题目 {question_num} 不存在")
            return
        
        # 生成答案图片
        image_path = render_admin_image(question_num)
        await admin_cmd.finish(Message([
            MessageSegment.text(f"第{question_num}题答案：\n"),
            MessageSegment.image(f"file:///{image_path}")
        ]))
    else:
        await admin_cmd.finish(f"未知命令：{command}\n可用命令：\n- clear: 清除所有用户的答题记录\n- answer 题号: 查看指定题目的答案")

@convert_cmd.handle()
async def handle_convert(event: MessageEvent):
    user_id = event.user_id
    state = db.get_user_state(user_id)
    if not state:
        await convert_cmd.finish("请先选择题目")
        return
    
    grid_num = db.get_user_question(user_id)
    if not grid_num or grid_num not in crossword_layouts:
        await convert_cmd.finish("请先选择题目")
        return
    
    grid_data, solved_questions, is_romaji = state
    grid_data = json.loads(grid_data)
    solved_questions = set(json.loads(solved_questions))
    
    # 创建游戏状态对象
    game_state = GameState(
        grid=[[GridCell(**cell) for cell in row] for row in grid_data],
        solved_questions=solved_questions,
        is_romaji=not is_romaji  # 切换显示模式
    )
    
    # 获取当前题目信息
    _, is_japanese, _ = crossword_layouts[grid_num]
    
    # 检查是否支持假名转换
    if not is_japanese:
        await convert_cmd.finish("当前题目不支持假名转换功能")
        return
    
    # 根据当前模式进行转换
    if not is_romaji:
        # 转换为罗马音
        for row in game_state.grid:
            for cell in row:
                if cell.content:
                    cell.content = convert_to_romaji(cell.content)
    else:
        # 转换回假名
        _, _, layout = crossword_layouts[grid_num]
        for direction, start_coord, length, q_num, answers in layout:
            if q_num in game_state.solved_questions:
                row = ord(start_coord[0].upper()) - ord('A')
                col = int(start_coord[1:]) - 1
                answer = answers[0]  # 使用假名形式
                for i in range(length):
                    if direction == "横":
                        game_state.grid[row][col + i].content = answer[i]
                    else:  # 竖
                        game_state.grid[row + i][col].content = answer[i]
    
    # 保存更新后的状态
    db.set_user_state(
        user_id,
        json.dumps([[cell.__dict__ for cell in row] for row in game_state.grid]),
        json.dumps(list(game_state.solved_questions)),
        game_state.is_romaji
    )
    
    # 生成并发送图片
    image_path = save_game_image(game_state, user_id)
    await convert_cmd.finish(Message([
        MessageSegment.text(f"已切换到{'罗马音' if game_state.is_romaji else '假名'}显示模式\n"),
        MessageSegment.image(f"file:///{image_path}")
    ]))

@pass_cmd.handle()
async def handle_pass(event: MessageEvent):
    user_id = event.user_id
    grid_num = db.get_user_question(user_id)
    if not grid_num:
        await pass_cmd.finish("请先选择题目")
        return
    
    # 添加到已尝试题目
    db.add_attempted_question(user_id, grid_num)
    
    # 清除用户状态
    db.set_user_question(user_id, 0)
    db.set_user_state(user_id, "[]", "[]", False)
    
    await pass_cmd.finish(f"已放弃第{grid_num}题")

@submit_cmd.handle()
async def handle_submit(event: MessageEvent):
    user_id = event.user_id
    grid_num = db.get_user_question(user_id)
    if not grid_num:
        await submit_cmd.finish("请先选择题目")
        return
    
    state = db.get_user_state(user_id)
    if not state:
        await submit_cmd.finish("请先回答题目")
        return
    
    grid_data, solved_questions, _ = state
    grid_data = json.loads(grid_data)
    solved_questions = set(json.loads(solved_questions))
    
    # 检查是否所有题目都已答对
    _, _, layout = crossword_layouts[grid_num]
    all_solved = all(q_num in solved_questions for _, _, _, q_num, _ in layout)
    
    if all_solved:
        # 如果是第二题，发送答案图片
        if grid_num == 2:
            answer_path = str(PIC_DIR / f"answer{grid_num}.png")
            # 清除当前题目状态
            db.set_user_question(user_id, 0)
            db.set_user_state(user_id, "[]", "[]", False)
            await submit_cmd.finish(Message([
                MessageSegment.text("恭喜你完成所有题目！\n"),
                MessageSegment.image(f"file:///{answer_path}"),
                MessageSegment.text("\n请使用 /选择题目 第X题 选择新的题目")
            ]))
        else:
            await submit_cmd.finish("恭喜你完成所有题目！")
    else:
        await submit_cmd.finish("还有题目未完成，请继续努力！")

@erase_cmd.handle()
async def handle_erase(event: MessageEvent):
    msg = event.get_plaintext().strip()
    
    # 检查消息格式
    if len(msg.split()) != 2:  # 命令 题号
        return await erase_cmd.send("格式错误，请使用：/擦除 题号（支持中文数字）")
        
    _, question_num = msg.split()
    
    # 检查用户是否选择了题目
    user_id = event.user_id
    grid_num = db.get_user_question(user_id)
    if not grid_num:
        return await erase_cmd.send("请先使用 /选择题目 第X题 选择要回答的题目")
    
    state = db.get_user_state(user_id)
    if not state:
        return await erase_cmd.send("请先回答题目")
    
    grid_data, solved_questions, is_romaji = state
    grid_data = json.loads(grid_data)
    solved_questions = set(json.loads(solved_questions))
    
    # 创建游戏状态对象
    game_state = GameState(
        grid=[[GridCell(**cell) for cell in row] for row in grid_data],
        solved_questions=solved_questions,
        is_romaji=bool(is_romaji)
    )
    
    # 在布局中查找对应的题目
    _, _, layout = crossword_layouts[grid_num]
    for direction, start_coord, length, q_num, _ in layout:
        if q_num == question_num:
            row = ord(start_coord[0].upper()) - ord('A')
            col = int(start_coord[1:]) - 1
            
            # 擦除答案
            for i in range(length):
                if direction == "横":
                    game_state.grid[row][col + i].content = ""
                else:  # 竖
                    game_state.grid[row + i][col].content = ""
            
            # 从已解答集合中移除
            if question_num in game_state.solved_questions:
                game_state.solved_questions.remove(question_num)
            
            # 保存更新后的状态
            db.set_user_state(
                user_id,
                json.dumps([[cell.__dict__ for cell in row] for row in game_state.grid]),
                json.dumps(list(game_state.solved_questions)),
                game_state.is_romaji
            )
            
            # 生成并发送图片
            image_path = save_game_image(game_state, user_id)
            return await erase_cmd.send(Message([
                MessageSegment.text(f"已擦除第{question_num}题的答案\n"),
                MessageSegment.image(f"file:///{image_path}")
            ]))
    
    return await erase_cmd.send(f"未找到第{question_num}题") 