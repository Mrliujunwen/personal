import json

for i in range(1,47):
    with open(f"data/merge_results/merged_asr_result{i}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        datas=data[0]["merged_sentences"]
    datajson=[]
    for j,item in enumerate(datas):
        if "朕" in item["text"]:
            print(item["text"])
            print(j)
            conversion={"orther":datas[j-1]["text"],"huang":item["text"]}
            datajson.append(conversion)

    with open(f"data/conversion_result/conversion_result{i}.json", "w", encoding="utf-8") as f:
        json.dump(datajson, f, ensure_ascii=False, indent=2)

