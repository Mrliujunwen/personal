import json
import ast
import os
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_and_save_asr_result(input_file, output_dir, json_filename="parsed_asr_result.json", txt_filename="parsed_asr_result.txt"):
    """
    解析ASR结果并保存到指定目录
    
    :param input_file: 输入的JSON文件路径
    :param output_dir: 输出目录路径
    :param json_filename: 输出的JSON文件名
    :param txt_filename: 输出的文本文件名
    :return: 成功返回True，失败返回False
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 读取JSON文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 解析文本数据
        text_data = ast.literal_eval(data['text'])
        
        # 准备保存结果
        results = []
        
        for item in text_data:
            item_result = {
                'key': item['key'],
                'text': item['text'],
                'sentences': []
            }
            
            for sentence in item['sentence_info']:
                item_result['sentences'].append({
                    'speaker': f"Speaker_{sentence['spk']}",
                    'text': sentence['text'],
                    'start_ms': sentence['start'],
                    'end_ms': sentence['end'],
                    # 'timestamps': sentence['timestamp']
                })
            
            results.append(item_result)
        
        # 保存解析结果到新文件
        output_file = os.path.join(output_dir, json_filename)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"解析结果已保存到: {output_file}")
        
        # 同时保存一个便于阅读的文本版本
        text_output_file = os.path.join(output_dir, txt_filename)
        with open(text_output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(f"\n=== 文件: {result['key']} ===\n")
                f.write(f"完整文本: {result['text'][:100]}...\n\n")
                
                for sent in result['sentences'][:5]:  # 只写入前5句示例
                    f.write(f"说话人: {sent['speaker']}\n")
                    f.write(f"时间段: {sent['start_ms']}-{sent['end_ms']}ms\n")
                    f.write(f"内容: {sent['text']}\n")
                    # f.write(f"时间戳: {sent['timestamps']}\n\n")
        
        logger.info(f"文本格式结果已保存到: {text_output_file}")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {e}")
    except (SyntaxError, ValueError) as e:
        logger.error(f"AST解析错误: {e}")
    except Exception as e:
        logger.error(f"发生未知错误: {e}")
    
    return False

def parse_arguments():
    """
    解析命令行参数
    
    :return: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='解析ASR结果并保存到指定目录')
    parser.add_argument('--input-prefix', '-i', type=str, default="data/asr_result",
                        help='输入的JSON文件前缀 (默认: data/asr_result)')
    parser.add_argument('--output', '-o', type=str, default="data/parsed_results",
                        help='输出目录路径 (默认: data/parsed_results)')
    parser.add_argument('--start', '-s', type=int, default=1,
                        help='起始文件编号 (默认: 1)')
    parser.add_argument('--end', '-e', type=int, default=46,
                        help='结束文件编号 (默认: 10)')
    parser.add_argument('--json-suffix', '-j', type=str, default=".json",
                        help='输出的JSON文件后缀 (默认: .json)')
    parser.add_argument('--txt-suffix', '-t', type=str, default=".txt",
                        help='输出的文本文件后缀 (默认: .txt)')
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    # 统计成功和失败的数量
    success_count = 0
    failure_count = 0
    
    # 循环处理文件
    for i in range(args.start, args.end + 1):
        input_file = f"{args.input_prefix}{i}.json"
        json_filename = f"parsed_asr_result{i}{args.json_suffix}"
        txt_filename = f"parsed_asr_result{i}{args.txt_suffix}"
        
        logger.info(f"正在处理文件: {input_file}")
        
        # 执行解析和保存
        success = parse_and_save_asr_result(
            input_file, 
            args.output,
            json_filename,
            txt_filename
        )
        
        if success:
            success_count += 1
            logger.info(f"文件 {input_file} 处理成功")
        else:
            failure_count += 1
            logger.error(f"文件 {input_file} 处理失败")
    
    # 输出统计结果
    logger.info(f"处理完成 - 成功: {success_count}, 失败: {failure_count}")
    if failure_count > 0:
        logger.error(f"有{failure_count}个文件处理失败")