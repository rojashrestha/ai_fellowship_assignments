# Model Optimization & Production Serving Report

## 1. Executive Summary
This document provides the technical analysis, justification, and recommendations for model optimization in production AI systems, specifically addressing **ONNX conversion applicability**, **Quantization techniques**, and **vLLM continuous batching**.

---

## 2. ONNX Conversion Analysis & Justification

### 2.1 What is ONNX?
The **Open Neural Network Exchange (ONNX)** is an open format built to represent machine learning models. ONNX Runtime (ORT) enables cross-platform hardware acceleration across CPUs, GPUs (via CUDA/TensorRT), and NPUs.

### 2.2 Applicability Matrix

| Model Class | ONNX Applicability | Performance Impact | Recommendation |
| :--- | :--- | :--- | :--- |
| **Embedding Models** (`all-MiniLM-L6-v2`, `bge-small-en`) | **Highly Applicable** | **2.5x - 4x speedup** on CPU/GPU inference; reduced memory footprint. | **Export to ONNX** using `optimum-cli` or `torch.onnx.export`. |
| **Cross-Encoder Rerankers** (`ms-marco-MiniLM-L-6-v2`) | **Highly Applicable** | **2x speedup** in RAG reranking stage. | **Export to ONNX** for low-latency scoring. |
| **Large Autoregressive LLMs** (e.g. Llama-3-8B, Mistral-7B) | **Limited / Not Recommended for High Throughput** | Complex KV-cache management, dynamic batching limitations in pure ONNX. | **Serve via vLLM / TensorRT-LLM** instead of raw ONNX. |

### 2.3 Justification: Why vLLM is Preferred over Raw ONNX for Generative LLMs
For large generative models ($>7\text{B}$ parameters), raw ONNX runtime does not natively provide:
1. **PagedAttention**: PagedAttention in vLLM manages KV-cache memory as virtual pages, eliminating 96% of memory fragmentation.
2. **Continuous (Iteration-Level) Batching**: Requests of varying output token lengths are batched dynamically at the token iteration level rather than waiting for the entire batch to complete.
3. **Decoupled Prefill and Decode**: Optimizes memory bandwidth saturation during decoding steps.

Therefore, the optimal hybrid strategy is:
- **Embedding / RAG Vectorization**: Optimized via **ONNX Runtime / INT8 quantization**.
- **Generative Assistant LLM**: Served via **vLLM (AWQ/GPTQ INT4)**.

---

## 3. Quantization Strategies

### 3.1 Quantization Techniques Overview
1. **AWQ (Activation-aware Weight Quantization)**:
   - Protects the top 1% salient weights based on activation magnitudes while quantizing remaining weights to 4-bit.
   - Preserves generation perplexity and reasoning capabilities almost identical to FP16.
2. **GPTQ (Generative Pre-trained Transformer Quantization)**:
   - One-shot second-order error compensation method for 4-bit weights.
   - Extremely fast kernel execution on NVIDIA GPUs.
3. **GGUF / llama.cpp**:
   - Best for CPU and mixed CPU/Metal/Vulkan execution on edge devices.

### 3.2 Memory and Throughput Comparison

| Model Precision | VRAM Required (8B Model) | Relative Inference Speed | Quality Retention (Perplexity) |
| :--- | :--- | :--- | :--- |
| **FP16 / BF16** | ~16 GB | 1.0x (Baseline) | 100% |
| **INT8 (BitsAndBytes)** | ~9 GB | 0.85x | 99.8% |
| **AWQ 4-Bit (vLLM)** | **~5.5 GB** | **2.2x** | **99.2%** |
| **GPTQ 4-Bit** | **~5.5 GB** | **2.0x** | **99.0%** |

---

## 4. Serving with vLLM in Docker

To serve an open-source model locally using vLLM in production:

```bash
docker run --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Meta-Llama-3-8B-Instruct \
    --quantization awq \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.90
```

The AI Assistant connects seamlessly to this container via `VLLM_BASE_URL=http://vllm:8000/v1`.
