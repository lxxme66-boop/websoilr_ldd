import os
import json
import pickle
import pandas as pd
import concurrent.futures
import argparse
import openai
from prompt_conf import build_prompt
def encode_img(img_path):
    import base64
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    img_type = img_path.split(".")[-1]
    return f"data:image/{img_type};base64,{img_base64}"
def load_data(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path).to_dict(orient="records")
    elif ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif ext in (".pkl", ".pickle"):
        with open(path, "rb") as f:
            return pickle.load(f)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def save_data(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def generate_new(record, model, temperature):
    record_reasoning = record["reasoning"]
    img_path = record["image"]
    new_record_template = build_prompt(record["question"],record["answer"])
    prompt = (
        "请基于以下输入生成新的数据记录，注意保持结构一致并补充必要字段：\n"
        f"{new_record_template}\n"
    )
    from openai import OpenAI,AsyncOpenAI
    client = AsyncOpenAI(base_url=openai.api_base, api_key=openai.api_key)
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": 
        [   
            {"type": "image_url", "image_url": {"url": encode_img(img_path)}
            },
            {"type":"text","text":prompt}
        ]}],
        temperature=temperature,
        max_tokens=8192
    )
    return resp.choices[0].message.content



def main():
    parser = argparse.ArgumentParser(
        description="使用 OpenAI 接口并发生成新数据记录"
    )
    parser.add_argument("--data-path", required=True,
                        help="输入数据文件路径（支持 .csv/.json/.pkl/.pickle）")
    parser.add_argument("--output-path", required=True,
                        help="结果输出 JSON 文件路径")
    parser.add_argument("--concurrency", type=int, default=5,
                        help="并发请求数，默认 5")
    parser.add_argument("--api-url", default="https://ark.cn-beijing.volces.com/api/v3",
                        help="OpenAI 接口地址")
    parser.add_argument("--model-name", default="ep-20250717164726-xgxnh",
                        help="使用模型名称，默认 gpt-4o-mini")
    parser.add_argument("--api-key", default = "ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b",
                        required=True,
                        help="你的 OpenAI API Key")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="生成的随机性温度，默认 0.7")

    args = parser.parse_args()

    openai.api_key = args.api_key
    openai.api_base = args.api_url

    data = load_data(args.data_path)
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {executor.submit(generate_new, rec, args.model_name, args.temperature): rec 
                   for rec in data}
        for fut in concurrent.futures.as_completed(futures):
            rec = futures[fut]
            try:
                out = fut.result()
                results.append(out)
            except Exception as e:
                print(f"Error processing record {rec}: {e}")

    save_data(results, args.output_path)
    print(f"Completed! Results saved to {args.output_path}")

if __name__ == "__main__":
    main()
