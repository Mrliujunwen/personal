import aiohttp
import asyncio
import logging
import json
from tqdm import tqdm
from datetime import datetime
import os


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
            data = {
                "model": "Qwen2.5",
                "messages": [
                    {"role": "user", "content":f"""
                     你现在来看一下这个内容，这个是orther说的{question["orther"]}，这是huang说的{question["huang"]}，
                    ，理论上这是一个对话，
                    ## 可能存在的错误
                    - 可能有错别字，如果有错别字就给我修改，但是原意不要修改
                    - 可能会有标点符号的错误，如果有，修改标点符号为正确的
                    ## 返回结果
                    - 这俩如果不是一个人和皇上的对话逻辑，那么就返回否
                    - 返回标准的json格式，不要给出其他任何数据
                     
                     {{
                     "result":"是"或者"否"//是否是皇上和orther的对话
                     "input":"修改后的内容"//如果是的话，而且有错别字就修改，如果不是的话就是原话，这是orther说的，里边只能放说的话，不要放其他内容
                     "output":"修改后的内容"//如果是的话，而且有错别字就修改，如果不是的话就是原话，这是huang说的，里边只能放说的话，不要放其他内容
                     }}
                     """}
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


async def main(input_file: str, output_file: str, max_concurrent: int = 5):
    """主函数"""
    # 读取输入文件
    questions = []
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
        with open(output_file, "w", encoding="utf-8") as f:
            for data in caller.datas:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

    logger.info("所有问题处理完成")


if __name__ == "__main__":
    for i in range(1,47):
        input_file = f"data/conversion_result/conversion_result{i}.json"
        output_file = f"data/qwenapi_result/qwenapi_result{i}.json"
        asyncio.run(main(input_file, output_file, max_concurrent=64))
