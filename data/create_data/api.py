import aiohttp
import asyncio
import logging
import json
from tqdm import tqdm
from datetime import datetime
import os
import random
from pathlib import Path
from typing import List, Dict, Any
# 现代角色库（可自由扩展）
MODERN_ROLES = [
    # 教育场景
    {"role": "高中生", "traits": ["青涩", "网络用语", "求知欲"], "examples": ["这道题怎么解？", "老师能不能划重点？"]},
    {"role": "大学教授", "traits": ["严谨", "学术化", "权威"], "examples": ["根据最新研究...", "这个理论有三个漏洞"]},
    {"role": "留学顾问", "traits": ["信息差", "焦虑贩卖", "话术套路"], "examples": ["背景提升很重要", "Top 50院校保录取"]},
    {"role": "网课助教", "traits": ["机械回复", "模板化", "拖延应对"], "examples": ["这个问题已记录", "请查看公告区FAQ"]},

    # 职场场景
    {"role": "程序员", "traits": ["直接", "技术术语", "务实"], "examples": ["这个需求有技术债", "API返回500错误"]},
    {"role": "HR经理", "traits": ["圆滑", "政策敏感", "协调"], "examples": ["公司目前headcount冻结", "你的期望薪资是？"]},
    {"role": "产品经理", "traits": ["画饼", "抽象需求", "甩锅倾向"], "examples": ["这个功能很简单", "技术实现我不管"]},
    {"role": "创业CEO", "traits": ["打鸡血", "融资术语", "风险转移"], "examples": ["我们在Pre-A轮", "期权比现金更有价值"]},
    {"role": "外包员工", "traits": ["卑微", "边界感强", "工时精确"], "examples": ["需求要加钱", "合同里没写这部分"]},

    # 日常生活
    {"role": "家庭主妇", "traits": ["生活化", "细节控", "情感化"], "examples": ["超市土豆涨价了", "孩子班主任来电话了"]},
    {"role": "健身教练", "traits": ["激励", "专业术语", "强势"], "examples": ["再做最后一组！", "你体脂率偏高"]},
    {"role": "广场舞领队", "traits": ["嗓门大", "辈分压制", "资源整合"], "examples": ["小王把音响搬过来", "李姐认识街道办的"]},
    {"role": "密室NPC", "traits": ["戏精", "规则守护", "突然惊吓"], "examples": ["欢迎来到亡灵古堡...", "禁止触碰道具！"]},
    {"role": "二手房东", "traits": ["话术陷阱", "临时加价", "装穷"], "examples": ["押金不退是行规", "我也要还房贷啊"]},

    # 新兴行业
    {"role": "带货主播", "traits": ["饥饿营销", "夸张表演", "价格对比"], "examples": ["最后三单秒杀！", "原价899今天99"]},
    {"role": "电竞选手", "traits": ["手速炫耀", "战术黑话", "年轻气盛"], "examples": ["这波我1v5", "对面打野在偷龙"]},
    {"role": "汉服妆娘", "traits": ["古风腔", "考据癖", "强迫症"], "examples": ["唐制襦裙不能配明制头饰", "你的发包没藏好"]},
    {"role": "宠物殡葬师", "traits": ["温柔克制", "仪式感强", "回避直白"], "examples": ["它只是去彩虹桥了", "可以留下爪印纪念"]},

    # 特殊群体
    {"role": "朝阳群众", "traits": ["警惕性高", "线索联想", "热心过度"], "examples": ["那家阳台有可疑盆栽", "我帮你联系居委会"]},
    {"role": "环球旅行家", "traits": ["凡尔赛", "攻略达人", "风险淡化"], "examples": ["叙利亚其实很安全", "办签证要准备20项材料"]},
    {"role": "玄学博主", "traits": ["模棱两可", "灾难预言", "付费解锁"], "examples": ["你命中有贵人相助", "详情请扫码咨询"]}
]
# 配置日志
def setup_logging(log_dir="./logs", log_level=logging.INFO, show_logs=True):
    """设置日志配置"""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/qwen7b_processing_{timestamp}.log"

    handlers = [logging.FileHandler(log_file, encoding='utf-8')]
    if show_logs:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

    return logging.getLogger()


logger = setup_logging()

async def analyze_feedback(feedback_content):
    """
    Analyze a single feedback entry using LLM
    """
    try:
        # Clean up the response if it contains code block formatting
        clean_response = feedback_content
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]  # Remove ```json prefix
        if clean_response.startswith('```'):
            clean_response = clean_response[3:]  # Remove ``` prefix
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]  # Remove ``` suffix
        if clean_response.startswith('```python'):
            clean_response = clean_response[7:]  # Remove ```json prefix
        if clean_response.startswith('```'):
            clean_response = clean_response[3:]  # Remove ``` prefix
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]  # Remove ``` suffix
        # Parse the cleaned JSON
        logger.info(f"clean_response: {clean_response}")
        result = json.loads(clean_response)
        logger.info(f"result: {result}")

        return result
    except Exception as e:
        clean_response = json.dumps(clean_response, ensure_ascii=False)
        return json.loads(clean_response)
async def generate_role_prompt(question):
    """生成带随机角色的prompt"""
    selected_role = random.choice(MODERN_ROLES)
    
    return f"""
## 角色
- 你是一个资深的语言大师，精通各行各业的语言
## 任务
- 我需要得到一些的和皇帝的对话
- 我现在会给你一个角色的相关信息，然后我给予你了一个对话的实例，你根据当前角色还可能的说的话或者相关问题，来生成提问以及皇帝的回答
- 提问需要按照当代的语言提问，也就是我给你的角色信息的few-shot的样子提问
## 角色信息
- 提问者身份：{selected_role['role']}
- 角色特征：{", ".join(selected_role['traits'])}
- 示例发言："{selected_role['examples']}"

## 当前对话
- 输入内容：「{question["input"]}」
- 皇帝回应：「{question["output"]}」

## 输出格式
- 标注json格式
- 不要输出其他任何东西
 {{
 "input":""//模仿的提问,注意使用当代语言提问，不要出现皇上两个字，就是角色信息的正常说话
"output":""//生成的回答
 }}
""".strip()
class AsyncQwenCaller:
    def __init__(self, max_concurrent=5, max_retries=3):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.url = "http://localhost:8001/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_TOKEN"
        }
        self._running_tasks = set()
        self.processed_count = 0
        self.total_count = 0
        self.progress_bar = None
        self.datas = []

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=600, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def _call_api(self, question: dict, retry_count=0) -> dict:
        """实际调用API的异步方法，带重试机制"""
        try:
            # print(generate_role_prompt(question))
            data = {
                "model": "Qwen2.5",
                "messages": [
                    {"role": "user", "content":await generate_role_prompt(question)}
                ],
                "temperature": 0.7,
                "max_tokens": 4096 * 4
            }

            async with self.session.post(self.url, headers=self.headers, json=data) as response:
                response_json = await response.json()
                response_data = response_json["choices"][0]["message"].get("content")
                logger.info(f"回答: {response_data}")
                logger.info("-" * 50)

                # question["answer_7b"] = response_data
                return response_data

        except Exception as e:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # 指数退避
                logger.warning(f"请求失败，{wait_time}秒后重试... (错误: {str(e)})")
                await asyncio.sleep(wait_time)
                return await self._call_api(question, retry_count + 1)
            logger.error(f"处理问题 '{question['question']}' 时发生错误: {str(e)}")
            return question

    async def _execute_call(self, question: dict, task_id: int):
        """实际执行调用的内部方法"""
        try:
            result = await self._call_api(question)
            result = await analyze_feedback(result)
            self.datas.append(result)
            if self.progress_bar:
                self.progress_bar.update(1)
                self.processed_count += 1
        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {str(e)}")
            if self.progress_bar:
                self.progress_bar.update(1)
                self.processed_count += 1

    async def process_question(self, question: dict, task_id: int):
        """处理单个问题"""
        while len(self._running_tasks) >= self.max_concurrent:
            done, _ = await asyncio.wait(
                self._running_tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            self._running_tasks -= done

        task = asyncio.create_task(self._execute_call(question, task_id))
        self._running_tasks.add(task)
        task.add_done_callback(self._running_tasks.discard)

    def set_progress_bar(self, total):
        """设置进度条"""
        self.total_count = total
        self.progress_bar = tqdm(total=total, desc="处理问题", unit="个")

    def close_progress(self):
        """关闭进度条"""
        if self.progress_bar:
            self.progress_bar.close()


async def main(input_file: str, output_dir: str, max_concurrent: int = 5, batch_size: int = 100):
    for j in range(batch_size):
        questions=[]
        with open(input_file, "r", encoding="utf-8") as f:
            data=json.load(f)
            for i in data:
                questions.append(i)
        # for line in f:
        #     try:
        #         question = json.loads(line)
        #         questions.append(question)
        #     except json.JSONDecodeError:
        #         logger.warning(f"跳过无效的JSON行: {line[:50]}...")

        logger.info(f"共读取 {len(questions)} 条问题记录")

        # 异步处理问题
        async with AsyncQwenCaller(max_concurrent=max_concurrent) as caller:
            caller.set_progress_bar(len(questions))

            tasks = []
            for i, question in enumerate(questions):
                task = caller.process_question(question, i + 1)
                tasks.append(task)

            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)

            # 等待剩余的任务完成
            if caller._running_tasks:
                await asyncio.wait(caller._running_tasks)

            caller.close_progress()

            # 写入结果
            batch_output = Path(output_dir) / f"batch_{j+1}.json"

            with open(batch_output, "w", encoding="utf-8") as f:
                for data in caller.datas:
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")

        logger.info(f"所有批次处理完成，共生成 {batch_size} 个batch文件")
if __name__ == "__main__":
   
    input_file = f"input/train_data.json"
    output_file = f"output"
    asyncio.run(main(input_file, output_file, max_concurrent=64,batch_size=1))
