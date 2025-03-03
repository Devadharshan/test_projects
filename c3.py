import torch
import os
from transformers import LlamaConfig, LlamaForCausalLM, LlamaTokenizer
from accelerate import load_checkpoint_and_dispatch

# Path to LLaMA model directory
MODEL_PATH = r"C:\path\to\llama-2-7b"

# Load tokenizer
tokenizer = LlamaTokenizer.from_pretrained(MODEL_PATH)

# Define LLaMA config manually (if missing)
config = LlamaConfig(
    vocab_size=32000, hidden_size=4096, num_hidden_layers=32,
    num_attention_heads=32, intermediate_size=11008, max_position_embeddings=2048
)

# Initialize model
model = LlamaForCausalLM(config)

# Load weights with CPU offloading
checkpoint_path = os.path.join(MODEL_PATH, "consolidated.00.pth")
model = load_checkpoint_and_dispatch(model, checkpoint_path, device_map="auto", offload_folder="offload")

# Move to half precision to save memory
model = model.to(torch.float16)

# Put model in evaluation mode
model.eval()

def generate_question(ticket_text, score_level):
    """Generate AI-based questions."""
    prompt = f"Generate a {score_level} difficulty question based on the ticket: {ticket_text}"
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_length=100)
    return tokenizer.decode(output[0], skip_special_tokens=True)