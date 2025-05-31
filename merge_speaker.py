import json

def merge_consecutive_speakers(input_file, output_file):
    """
    合并连续的相同说话人的句子
    
    :param input_file: 输入的JSON文件路径（absdata.py处理后的结果）
    :param output_file: 输出的JSON文件路径
    """
    # 读取原始数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    merged_results = []
    
    for item in data:
        sentences = item.get('sentences', [])
        merged_sentences = []
        current_group = None
        
        for sentence in sentences:
            # 如果是第一句话或者说话人变了，创建新组
            if (current_group is None or 
                current_group['speaker'] != sentence['speaker'] or
                # 如果时间间隔超过2秒（2000ms），也视为新的对话
                sentence['start_ms'] - current_group['end_ms'] > 2000):
                
                if current_group is not None:
                    merged_sentences.append(current_group)
                
                current_group = {
                    'speaker': sentence['speaker'],
                    'text': sentence['text'],
                    'start_ms': sentence['start_ms'],
                    'end_ms': sentence['end_ms'],
                    'segments': [{
                        'text': sentence['text'],
                        'start_ms': sentence['start_ms'],
                        'end_ms': sentence['end_ms']
                    }]
                }
            else:
                # 合并连续的对话
                current_group['text'] += ' ' + sentence['text']
                current_group['end_ms'] = sentence['end_ms']
                current_group['segments'].append({
                    'text': sentence['text'],
                    'start_ms': sentence['start_ms'],
                    'end_ms': sentence['end_ms']
                })
        
        # 添加最后一组
        if current_group is not None:
            merged_sentences.append(current_group)
        
        # 创建新的结果项
        merged_item = {
            'key': item.get('key', ''),
            'text': item.get('text', ''),
            'merged_sentences': merged_sentences
        }
        merged_results.append(merged_item)
    
    # 保存合并后的结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_results, f, ensure_ascii=False, indent=2)
    
    # 同时生成一个易读的文本版本
    text_output = output_file.rsplit('.', 1)[0] + '.txt'
    with open(text_output, 'w', encoding='utf-8') as f:
        for item in merged_results:
            f.write(f"\n=== 文件: {item['key']} ===\n\n")
            
            for sentence in item['merged_sentences']:
                f.write(f"speaker: {sentence['speaker']}\n")
                f.write(f"datas: {sentence['start_ms']}-{sentence['end_ms']}ms\n")
                f.write(f"sentence: {sentence['text']}\n")
                # f.write("\n原始片段:\n")
                # for segment in sentence['segments']:
                #     f.write(f"  - {segment['text']} ({segment['start_ms']}-{segment['end_ms']}ms)\n")
                f.write("\n")
            f.write("-" * 80 + "\n")

if __name__ == "__main__":
    for i in range(1, 47):
        input_file = f"data/parsed_results/parsed_asr_result{i}.json"
        output_file = f"data/merge_results/merged_asr_result{i}.json"
        merge_consecutive_speakers(input_file, output_file)
        print(f"处理完成！\n结果已保存到: {output_file}\n文本版本保存到: {output_file.rsplit('.', 1)[0] + '.txt'}") 