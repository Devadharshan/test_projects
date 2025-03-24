from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import subprocess
import os
import json
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = FastAPI()

# Configure logging
logging.basicConfig(filename='logs/app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Load microservice-repo mapping
with open('conf.json', 'r') as f:
    service_repo_map = json.load(f)

# Load Open-LLaMA model
model_path = 'open_llama_model'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map="auto")

@app.post("/analyze/")
async def analyze_hprof(file: UploadFile = File(...), service_name: str = Form(...), prompt: str = Form(...)):
    # Save uploaded file
    hprof_path = f"dumps/{file.filename}"
    with open(hprof_path, "wb") as f:
        f.write(await file.read())

    # Determine repository URL from service name
    repo_url = service_repo_map.get(service_name)
    if not repo_url:
        logging.error(f"Service name '{service_name}' not found in configuration.")
        return JSONResponse(content={"error": "Service not found"}, status_code=400)

    # Run Java HPROF Analyzer
    output_json_path = f"analysis_results/{file.filename}.json"
    try:
        subprocess.run(
            ["java", "-cp", "java-hprof-analyzer/build:java-hprof-analyzer/lib/*", "com.example.analyzer.HprofAnalyzer", hprof_path, output_json_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Java analyzer failed: {e}")
        return JSONResponse(content={"error": "Java analyzer failed"}, status_code=500)

    # Read analysis results
    with open(output_json_path, 'r') as f:
        analysis_data = json.load(f)

    # Prepare input for AI model
    ai_input = f"Repository URL: {repo_url}\nPrompt: {prompt}\nAnalysis Data: {json.dumps(analysis_data)}"

    # Tokenize and generate response
    inputs = tokenizer(ai_input, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=200)
    ai_response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Log and return response
    logging.info(f"Analysis completed for {file.filename} with service {service_name}")
    return JSONResponse(content={"analysis": analysis_data, "ai_response": ai_response})
