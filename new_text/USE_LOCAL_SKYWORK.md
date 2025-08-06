# 使用本地 Skywork-R1V3-38B 模型

既然您本地已经有 Skywork-R1V3-38B 模型，您需要修改以下配置：

## 1. 修改 config.json

将以下部分进行修改：

### API配置部分
```json
"api": {
    "ark_url": "http://localhost:8080/v1",  // 改为localhost
    "use_local_models": true,
    "local_model_priority": ["vllm", "transformers", "ollama"]  // vllm优先
}
```

### vLLM配置部分
```json
"vllm": {
    "enabled": true,  // 改为true
    "base_url": "http://localhost:8080",  // 改为8080端口
    "model_name": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",  // 使用本地路径
    "timeout": 600
}
```

### Transformers配置部分
```json
"transformers": {
    "enabled": true,  // 改为true
    "model_name": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",  // 使用本地路径
    "device": "auto",
    "torch_dtype": "auto",
    "load_in_4bit": false,
    "load_in_8bit": true  // 使用8位量化减少显存
}
```

## 2. 使用方法

### 方案A：使用vLLM（推荐）

1. 安装vLLM：
```bash
pip install vllm
```

2. 启动vLLM服务：
```bash
python -m vllm.entrypoints.openai.api_server \
    --model /mnt/storage/models/Skywork/Skywork-R1V3-38B \
    --host 0.0.0.0 \
    --port 8080 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9
```

3. 运行程序：
```bash
python run_pipeline.py --input_path data/texts --use_local_models
```

### 方案B：使用Transformers

1. 安装依赖：
```bash
pip install transformers torch accelerate bitsandbytes
```

2. 直接运行：
```bash
python run_pipeline.py --input_path data/texts --use_local_models --model_type transformers
```

## 3. 为什么还需要setup_ollama.sh？

- setup_ollama.sh 是为了提供一个轻量级的备用方案
- 当Skywork模型不可用或显存不足时，可以使用Ollama运行较小的模型
- 这是一个多层次的容错设计，确保系统的高可用性

## 4. 注意事项

- Skywork-R1V3-38B 需要大量GPU显存（建议40GB+）
- 如果显存不足，可以使用8位量化
- vLLM提供更好的推理性能
- 确保端口8080没有被其他服务占用
