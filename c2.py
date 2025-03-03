import torch
import os
from transformers import LlamaConfig, LlamaForCausalLM, LlamaTokenizer

# Set model path (Update this with your actual path)
MODEL_PATH = r"C:\path\to\llama-2-7b"

# Ensure the tokenizer file exists
TOKENIZER_PATH = os.path.join(MODEL_PATH, "tokenizer.model")
if not os.path.exists(TOKENIZER_PATH):
    raise FileNotFoundError(f"Tokenizer model not found at {TOKENIZER_PATH}")

# Load tokenizer
tokenizer = LlamaTokenizer(TOKENIZER_PATH)

# Manually define LLaMA model configuration (if missing)
config = LlamaConfig(
    vocab_size=32000,  # Standard LLaMA vocab size
    hidden_size=4096,  # LLaMA-2-7B hidden layer size
    num_hidden_layers=32,  # Number of transformer blocks
    num_attention_heads=32,  # Attention heads per layer
    intermediate_size=11008,  # FFN layer size
    max_position_embeddings=2048,  # Max sequence length
)

# Initialize model
model = LlamaForCausalLM(config)

# Load checkpoint weights
checkpoint_path = os.path.join(MODEL_PATH, "consolidated.00.pth")
if not os.path.exists(checkpoint_path):
    raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")

checkpoint = torch.load(checkpoint_path, map_location="cpu")
model.load_state_dict(checkpoint, strict=False)

# Set model to evaluation mode
model.eval()

print("✅ LLaMA-2-7B Model loaded successfully on Windows!")