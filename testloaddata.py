import json
with open("data/conversion_result/conversion_result1.json", "r", encoding="utf-8") as f:
    data=json.load(f)
    for i in data:
        print(i["orther"])
        print(i["huang"])
        print("--------------------------------")
