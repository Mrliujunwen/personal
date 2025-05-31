import json
import os

base_dir = "data/qwenapi_result"
data_list = []
for file in os.listdir(base_dir):
    print(file)
    if file=="qwenapi_result.json":
        continue
    with open(os.path.join(base_dir, file), "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
            
                print(data)

                if data["result"] == "是":
                    data_list.append({"instruction":"",
                                    "input":data["input"],
                                    "output":data["output"]})
            except Exception as e:
                continue
with open("data/qwenapi_result/qwenapi_result.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, ensure_ascii=False, indent=4)

