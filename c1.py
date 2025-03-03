import torch
from transformers import LlamaForCausalLM, LlamaTokenizer

# ---- Load Model Checkpoint ----
MODEL_PATH = "models/llama-2-7b"

tokenizer = LlamaTokenizer.from_pretrained(MODEL_PATH)

# Load the model from checkpoint
checkpoint = torch.load(f"{MODEL_PATH}/consolidated.00.pth", map_location="cpu")

model = LlamaForCausalLM.from_pretrained(
    MODEL_PATH,
    state_dict=checkpoint,
    torch_dtype=torch.float16,  # Change to torch.float32 if running on CPU
    device_map="auto"  # Adjust based on your system
)

print("Model loaded prompt = f"""
Generate a {score_level} difficulty question for an engineer supporting {sample_ticket['application']}.
Analyze the following ticket details:

- **Issue Summary:** {sample_ticket['short_description']}
- **Long Description:** {sample_ticket['long description']}
- **Message to User:** {sample_ticket['message to user']}
- **Resolution Notes:** {sample_ticket['close notes']}

The question should assess the engineer’s ability to troubleshoot and resolve similar issues.
"""






