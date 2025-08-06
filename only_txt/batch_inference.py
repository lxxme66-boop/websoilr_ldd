import asyncio
import json
import multiprocessing
from typing import Any, Dict, Optional
import httpx
from volcenginesdkarkruntime import AsyncArk
from volcenginesdkarkruntime._constants import CLIENT_REQUEST_HEADER
api_key = "ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b"

def main(
    num_worker_processes: int,
    max_concurrency_per_process: int,
    model: str,
    api_key: Optional[str] = None,
) -> None:
    """
    多进程处理火山方舟批量推理接入点的并发请求（纯文本版本）。启动 `num_worker_processes + 2` 个进程，其中一个进程用于读取输入，另一个进程用于处理输出，
    其余进程用于任务处理并将结果放置在输出队列中。
    如果您要在实际应用中使用，需要根据您的实际情况调整 `read_input` 和 `write_output` 的实现。
    这里为了通用性考虑，使用单独的进程分别处理输入和输出，实际应用中可以根据需要进行调整。尽量减少进程间的通信，使用进程内的通信机制。
    例如，如果您的输入是文件读取的，您可以先将文件分为 `num_worker_processes` 个规模接近的文件，然后在每个 worker 进程中读取一个文件。
    同样地，如果您的输出是写入文件的，您可以每个worker 进程中都将结果写入一个文件，最终再将所有输出文件合并。
    又例如，如果您的输入从消息队列中读取，您可以使用同一个 consumer group 分别在每个 worker 进程中读取消息。
    同样地，如果您的输出是写入到消息队列，您可以在每个 worker 进程将处理结果直接写入。
    Args:
        num_worker_processes (int): 启动的子进程数，建议初始设置为 cpu 核心数的 2~4 倍
        max_concurrency_per_process (int): 每个子进程的最大并发数，我自己测试单进程比较合理的值是 256/512, 根据实际情况调整
        model (str): 方舟的 Endpoint ID, 可以在控制台查看
        api_key (str): 方舟的 API Key, 可以在控制台查看，建议直接在环境变量中设置，避免泄漏
    """
    processes = []
    in_queue: "multiprocessing.Queue[Optional[Dict[str, Any]]]" = multiprocessing.Queue(
        maxsize=512
    )
    out_queue: "multiprocessing.Queue[Optional[Dict[str, Any]]]" = (
        multiprocessing.Queue(maxsize=512)
    )
    # 启动 `num_worker_processes` 个子进程，每个子进程都从输入队列中读取输入，并将结果放置在输出队列中
    for i in range(num_worker_processes):
        p = multiprocessing.Process(
            target=process,
            args=(
                i,
                max_concurrency_per_process,
                api_key,
                in_queue,
                out_queue,
            ),
        )
        p.start()
        processes.append(p)

    # 启动一个子进程，用于读取输入并将输入放置在输入队列中
    read_process = multiprocessing.Process(target=read_input, args=(in_queue,))
    read_process.start()
    processes.append(read_process)

    # 启动一个子进程，用于从输出队列中读取输出并处理输出
    write_process = multiprocessing.Process(target=write_output, args=(out_queue,))
    write_process.start()
    processes.append(write_process)

    # 等待所有子进程结束
    for p in processes:
        p.join()


def read_input(in_queue: "multiprocessing.Queue[Optional[Dict[str, Any]]]") -> None:
    """
    从输入源读取输入并将输入放置在输入队列中（纯文本版本）
    这里是一个简单的示例，实际应用中需要根据您的输入源进行调整
    """
    import json
    import os
    
    # 示例：从JSON文件读取文本数据
    input_file = "data/text_input.json"
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found, creating sample data...")
        # 创建示例数据
        sample_data = [
            {
                "id": f"text_{i}",
                "content": f"这是第{i}个文本内容，用于测试批量处理功能。包含一些技术术语如TFT、OLED、显示器等。",
                "context": f"技术文档第{i}章节"
            }
            for i in range(100)
        ]
        os.makedirs("data", exist_ok=True)
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            # 将文本数据放入队列
            in_queue.put({
                "text_id": item.get("id", "unknown"),
                "text_content": item.get("content", ""),
                "context": item.get("context", ""),
                "metadata": {
                    "source": "text_file",
                    "processing_type": "text_analysis"
                }
            })
        
        print(f"Successfully queued {len(data)} text items for processing")
        
    except Exception as e:
        print(f"Error reading input: {e}")
    
    finally:
        # 发送结束信号
        for _ in range(multiprocessing.cpu_count()):
            in_queue.put(None)


def write_output(out_queue: "multiprocessing.Queue[Optional[Dict[str, Any]]]") -> None:
    """
    从输出队列中读取输出并处理输出（纯文本版本）
    这里是一个简单的示例，实际应用中需要根据您的输出需求进行调整
    """
    import json
    import os
    
    results = []
    output_file = "data/text_analysis_results.json"
    os.makedirs("data", exist_ok=True)
    
    while True:
        try:
            result = out_queue.get(timeout=10)
            if result is None:
                break
            
            results.append(result)
            print(f"Processed text analysis result: {result.get('text_id', 'unknown')}")
            
            # 定期保存结果
            if len(results) % 10 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"Saved {len(results)} results to {output_file}")
                
        except Exception as e:
            print(f"Error in write_output: {e}")
            break
    
    # 最终保存
    if results:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Final save: {len(results)} results to {output_file}")


def process(
    worker_id: int,
    max_concurrency: int,
    api_key: str,
    in_queue: "multiprocessing.Queue[Optional[Dict[str, Any]]]",
    out_queue: "multiprocessing.Queue[Optional[Dict[str, Any]]]",
) -> None:
    """
    工作进程：从输入队列中读取文本数据，进行处理，并将结果放置在输出队列中
    """
    print(f"Worker {worker_id} started with max_concurrency={max_concurrency}")
    
    async def worker():
        semaphore = asyncio.Semaphore(max_concurrency)
        tasks = []
        
        while True:
            try:
                # 从队列获取任务
                item = in_queue.get(timeout=1)
                if item is None:
                    break
                
                # 创建处理任务
                task = process_text_item(semaphore, item, api_key, worker_id)
                tasks.append(task)
                
                # 批量处理任务
                if len(tasks) >= max_concurrency:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if result is not None and not isinstance(result, Exception):
                            out_queue.put(result)
                    tasks = []
                    
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                continue
        
        # 处理剩余任务
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if result is not None and not isinstance(result, Exception):
                    out_queue.put(result)
    
    # 运行异步工作循环
    asyncio.run(worker())
    print(f"Worker {worker_id} finished")


async def process_text_item(
    semaphore: asyncio.Semaphore,
    item: Dict[str, Any],
    api_key: str,
    worker_id: int
) -> Optional[Dict[str, Any]]:
    """
    处理单个文本项目
    """
    async with semaphore:
        try:
            # 创建异步客户端
            client = AsyncArk(api_key=api_key)
            
            # 准备文本分析提示
            system_prompt = "你是一位显示半导体专家，请对给定的文本内容进行专业分析。"
            
            user_prompt = f"""
            请分析以下文本内容：
            
            文本内容：{item.get('text_content', '')}
            上下文：{item.get('context', '')}
            
            请提供：
            1. 关键概念提取
            2. 技术要点分析
            3. 专业术语解释
            4. 内容摘要
            
            请以JSON格式返回分析结果。
            """
            
            # 调用API
            response = await client.chat.completions.create(
                model="doubao-1.5-thinking-pro-m-250428",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2048
            )
            
            # 提取响应内容
            content = response.choices[0].message.content if response.choices else ""
            
            result = {
                "text_id": item.get("text_id"),
                "original_content": item.get("text_content"),
                "context": item.get("context"),
                "analysis_result": content,
                "worker_id": worker_id,
                "processing_status": "success",
                "metadata": item.get("metadata", {})
            }
            
            return result
            
        except Exception as e:
            print(f"Error processing text item {item.get('text_id')}: {e}")
            return {
                "text_id": item.get("text_id"),
                "processing_status": "error",
                "error_message": str(e),
                "worker_id": worker_id
            }


def run_text_batch_processing(
    num_workers: int = 4,
    max_concurrency: int = 256,
    model: str = "doubao-1.5-thinking-pro-m-250428"
):
    """
    运行文本批量处理的便捷函数
    """
    print(f"Starting text batch processing with {num_workers} workers, {max_concurrency} max concurrency")
    main(
        num_worker_processes=num_workers,
        max_concurrency_per_process=max_concurrency,
        model=model,
        api_key=api_key
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Text Batch Processing")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker processes")
    parser.add_argument("--concurrency", type=int, default=256, help="Max concurrency per process")
    parser.add_argument("--model", type=str, default="doubao-1.5-thinking-pro-m-250428", help="Model name")
    
    args = parser.parse_args()
    
    run_text_batch_processing(
        num_workers=args.workers,
        max_concurrency=args.concurrency,
        model=args.model
    )