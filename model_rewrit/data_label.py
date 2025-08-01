import os
import json
import pandas as pd
import concurrent.futures
import argparse
import openai


def load_input(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path).to_dict(orient="records")
    elif ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported input file type: {ext}")


def save_output(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_mpo(record, model, temperature, sample_size):
    # Step 1: 高温采样生成多条候选回答
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": record['subjective_question']}
        ],
        temperature=temperature,
        max_tokens=256,
        n=sample_size
    )
    samples = [choice.message.content.strip() for choice in resp.choices]
    # Step 2: 对每条候选回答进行判断，标注 positive/negative
    labeled = []
    for sample in samples:
        judge_prompt = f"""
    你是一名资深的数据标注与教学设计专家，熟悉MPO算法中偏好数据构造方法。
    请判断以下候选回答是否与参考答案保持一致。
    客观题: {record['objective_question']}
    参考答案: {record['reference_answer']}
    主观题: {record['subjective_question']}
    候选回答: {sample}
    若与参考答案对齐，label置为positive；否则置为negative。
    输出严格符合JSON格式，包含response和label字段：
    {{"response": "...", "label": "positive"或"negative"}}
    """
        jr = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": judge_prompt}],
            temperature=0.0,
            max_tokens=50
        )
        try:
            jr_json = json.loads(jr.choices[0].message.content.strip())
            label = jr_json.get("label", "negative")
        except json.JSONDecodeError:
            label = "negative"
        labeled.append({"response": sample, "label": label})
    return {
        "objective_question": record.get("objective_question"),
        "reference_answer": record.get("reference_answer"),
        "subjective_question": record.get("subjective_question"),
        "samples": labeled
    }


def main():
    parser = argparse.ArgumentParser(description="使用 OpenAI 构造 MPO 偏好数据（高温采样 + 判别）")
    parser.add_argument("--input-path", required=True,
                        help="输入文件路径，支持 .csv 或 .json，需包含objective_question, reference_answer, subjective_question字段")
    parser.add_argument("--output-path", required=True,
                        help="输出 JSON 文件路径，保存 MPO 样本列表")
    parser.add_argument("--model-name", default="gpt-4o-mini",
                        help="OpenAI 模型名称，默认 gpt-4o-mini")
    parser.add_argument("--api-key", required=True,
                        help="OpenAI API Key")
    parser.add_argument("--api-url", default="https://api.openai.com/v1",
                        help="OpenAI API 基础URL，支持私有部署")
    parser.add_argument("--concurrency", type=int, default=5,
                        help="并发处理记录数，默认5")
    parser.add_argument("--temperature", type=float, default=1.0,
                        help="采样温度，默认1.0 用于高温采样")
    parser.add_argument("--samples", type=int, default=5,
                        help="每条主观题采样的候选回答数量，默认5")
    args = parser.parse_args()

    openai.api_key = args.api_key
    openai.api_base = args.api_url

    records = load_input(args.input_path)
    mpo_data = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(
                generate_mpo, rec, args.model_name, args.temperature, args.samples
            ): rec for rec in records
        }
        for fut in concurrent.futures.as_completed(futures):
            try:
                mpo_data.append(fut.result())
            except Exception as e:
                rec = futures[fut]
                print(f"Error processing {rec}: {e}")

    save_output(mpo_data, args.output_path)
    print(f"MPO data generation completed. Saved {len(mpo_data)} records to {args.output_path}")

if __name__ == "__main__":
    main()
