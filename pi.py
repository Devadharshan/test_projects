project-root/
├── backend/
│   ├── HprofAnalyzer.java
│   ├── main.py
│   ├── requirements.txt
│   └── repo_mapping.json
└── frontend/
    ├── public/
    │   └── threejs/
    │       └── animation.js
    ├── pages/
    │   ├── index.js
    │   └── api/
    │       └── analyze.js
    └── package.
    
import os
import subprocess
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from llama_cpp import Llama

app = FastAPI()

# Load Open-LLaMA-2-7B model
model_path = "./models/ggml-model-q8_0.bin"
llama = Llama(model_path=model_path)

# Load microservice repository mapping
with open('repo_mapping.json') as f:
    repo_mapping = json.load(f)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), microservice: str = Form(...)):
    try:
        # Save the uploaded Hprof file
        hprof_path = f"./uploads/{file.filename}"
        with open(hprof_path, 'wb') as f:
            f.write(await file.read())

        # Run the Java Hprof Analyzer
        java_class = "HprofAnalyzer"
        output_json_path = f"./outputs/{file.filename}.json"
        subprocess.run(['java', java_class, hprof_path, output_json_path], check=True)

        return {"message": "File processed successfully.", "output_json": output_json_path, "microservice": microservice}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/")
async def analyze(prompt: str = Form(...), output_json: str = Form(...), microservice: str = Form(...)):
    try:
        # Load the analysis data from the JSON file
        with open(output_json, 'r') as f:
            analysis_data = json.load(f)

        # Extract relevant information
        summary = analysis_data.get('summary', 'No summary available.')
        leak_suspects = analysis_data.get('leakSuspects', 'No leak suspects identified.')

        # Prepare prompt for LLaMA model
        full_prompt = (
            f"Microservice: {microservice}\n"
            f"Repository Path: {repo_mapping.get(microservice, 'Not found')}\n\n"
            f"Heap Analysis Summary:\n{summary}\n\n"
            f"Leak Suspects:\n{leak_suspects}\n\n"
            f"User Prompt:\n{prompt}\n\n"
            "Based on the above information, provide suggestions to improve memory usage and performance."
        )

        # Generate AI suggestions
        response = llama(full_prompt, max_tokens=150)
        suggestions = response['choices'][0]['text'].strip()

        return {"suggestions": suggestions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str({
  "name": "frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "latest",
    "react": "latest",
    "react-dom": "latest",
    "three": "import { useState } from 'react';

export default function Home() {
    const [file, setFile] = useState(null);
    const [microservice, setMicroservice] = useState('microserviceA');
    const [prompt, setPrompt] = useState('');
    const [suggestions, setSuggestions] = useState('');

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleUpload = async () => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('microservice', microservice);

        const response = await fetch('http://localhost:8000/upload/', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();
        if (data.output_json) {
            handleAnalyze(data.output_json);
        }
    };

    const handleAnalyze = async (outputJson) => {
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('output_json', outputJson);
        formData.append('microservice', microservice);

        const response = await fetch('http://localhost:8000/analyze/', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();
        setSuggestions(data.suggestions);
    };

    return (
        <div>
            <h1>Hprof Analyzer</h1>
            <input type="file" onChange={handleFileChange} />
            <select value={microservice} onChange={(e) => setMicroservice(e.target.value)}>
                <option value="microserviceA">Microservice A</option>
                <option value="microserviceB">Microservice B</option>
            </select>
            <button onClick={handleUpload}>Upload and Analyze</button>
            <textarea
                placeholder="Enter your prompt import { useState } from 'react';

export default function Home() {
  const [file, setFile] = useState(null);
  const [microservice, setMicroservice] = useState('microserviceA');
  const [prompt, setPrompt] = useState('');
  const [suggestions, setSuggestions] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file to upload.');
      return;
    }

    setLoading(true);
    setSuggestions('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('microservice', microservice);

    try {
      const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('File upload failed.');
      }

      const uploadData = await uploadResponse.json();

      const analyzeResponse = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          output_json: uploadData.output_json,
          microservice: microservice,
        }),
      });

      if (!analyzeResponse.ok) {
        throw new Error('Analysis failed.');
      }

      const analyzeData = await analyzeResponse.json();
      setSuggestions(analyzeData.suggestions);
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Hprof Analyzer</h1>
      <div>
        <label>
          Select Hprof File:
          <input type="file" onChange={handleFileChange} />
        </label>
      </div>
      <div>
        <label>
          Select Microservice:
          <select
            value={microservice}
            onChange={(e) => setMicroservice(e.target.value)}
          >
            <option value="microserviceA">Microservice A</option>
            <option value="microserviceB">Microservice B</option>
          </select>
        </label>
      </div>
      <div>
        <label>
          Enter Prompt:
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt here..."
          />
        </label>
      </div>
      <div>
        <button onClick={handleUpload} disabled={loading}>
          {loading ? 'Processing...' : 'Upload and Analyze'}
        </button>
      </div>
      {suggestions && (
        <div>
          <h2>AI Suggestions:</h2>
          <p>{suggestions}</p>
        </div>
      )}
    </div>
  );
}




































