# Available Nemotron Models for LLM_MODEL

Copy any of these exact model names into your .env file:

## 🆕 Latest Nemotron V2 Models (Recommended)
```bash
# Fast & Efficient (9B parameters)
LLM_MODEL=nvidia/NVIDIA-Nemotron-Nano-9B-v2

# Better Quality (12B parameters)  
LLM_MODEL=nvidia/NVIDIA-Nemotron-Nano-12B-v2

# Base models for fine-tuning
LLM_MODEL=nvidia/NVIDIA-Nemotron-Nano-9B-v2-Base
LLM_MODEL=nvidia/NVIDIA-Nemotron-Nano-12B-v2-Base
```

## 🧠 Reasoning Specialists
```bash
# Best for planning and logic
LLM_MODEL=nvidia/OpenReasoning-Nemotron-7B
LLM_MODEL=nvidia/OpenReasoning-Nemotron-14B
LLM_MODEL=nvidia/OpenReasoning-Nemotron-32B
```

## 🦙 Llama Nemotron Series
```bash
# High performance (50B parameters)
LLM_MODEL=nvidia/Llama-3_3-Nemotron-Super-49B-v1_5

# Ultra large (253B parameters)
LLM_MODEL=nvidia/Llama-3_1-Nemotron-Ultra-253B-v1

# Classic 70B model
LLM_MODEL=nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
```

## 🏆 Reward Models (for evaluation)
```bash
LLM_MODEL=nvidia/Llama-3.3-Nemotron-70B-Reward
LLM_MODEL=nvidia/Llama-3_3-Nemotron-Super-49B-GenRM
```

## 📏 Long Context Models
```bash
# For very long documents
LLM_MODEL=nvidia/Llama-3.1-Nemotron-8B-UltraLong-1M-Instruct
LLM_MODEL=nvidia/Llama-3.1-Nemotron-8B-UltraLong-2M-Instruct
LLM_MODEL=nvidia/Llama-3.1-Nemotron-8B-UltraLong-4M-Instruct
```

## 🔄 Hybrid Models
```bash
# Mamba-Transformer hybrid
LLM_MODEL=nvidia/Nemotron-H-8B-Reasoning-128K
LLM_MODEL=nvidia/Nemotron-H-47B-Reasoning-128K
```

## 📚 Classic Nemotron 4
```bash
# Original large model
LLM_MODEL=nvidia/Nemotron-4-340B-Instruct
LLM_MODEL=nvidia/Nemotron-4-340B-Base
```

## 🔧 Embedding Models (for RAG)
```bash
# Text embeddings
LLM_MODEL=nvidia/llama-embed-nemotron-8b
LLM_MODEL=nvidia/omni-embed-nemotron-3b
```

---

## 🎯 My Recommendations by Use Case:

**🚀 Hackathon Demo**: `nvidia/NVIDIA-Nemotron-Nano-9B-v2`
**🧠 Planning Tasks**: `nvidia/OpenReasoning-Nemotron-7B`  
**💪 Best Quality**: `nvidia/Llama-3_3-Nemotron-Super-49B-v1_5`
**⚡ Fastest**: `nvidia/NVIDIA-Nemotron-Nano-9B-v2`
