pip install fastapi uvicorn llama-cpp-python

uvicorn app:app --reload
-----

Frontend Setup
1. Initialize Next.js Project:

Navigate to the frontend directory and initialize a new Next.js project:

npx create-next-app@latest .
2. Install Dependencies:

Install necessary packages, including three for Three.js and @react-three/fiber for React Three Fiber:

npm install three @react-three/fiber @react-three/drei
3. next.config.js:

Configure Next.js to allow loading of .glb files:

module.exports = {
  webpack(config) {
    config.module.rules.push({
      test: /\.glb$/,
      use: {
        loader: 'file-loader',
      },
    });
    return config;
  },
};
4. components/FileUpload.js:

Component for file upload with animation.

import { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, useGLTF } from '@react-three/drei';

function UploadAnimation() {
  const { scene } = useGLTF('/models/upload_animation.glb');
  return <primitive object={scene} />;
}

export default function FileUpload({ onUpload }) {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = () => {
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      <Canvas>
        <ambientLight />
        <OrbitControls />
        <UploadAnimation />
      </Canvas>
    </div>
  );
}
5. components/PromptInput.js:

Component for prompt input.

import { useState } from 'react';

export default function PromptInput({ onSubmit }) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = () => {
    onSubmit(prompt);
  };

  return (
    <div>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter your prompt here..."
      />
      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
}
6. components/ServiceSelector.js:

Component to select a microservice.

import { useState, useEffect } from 'react';

export default function ServiceSelector({ onSelect }) {
  const [services, setServices] = useState([]);

  useEffect(() => {
    fetch('/api/services')
      .then((res) => res.json())
      .then((data) => setServices(data.services));
  }, []);

  return (
    <div>
      <select onChange
::contentReference[oaicite:0]{index=0}
 
------
  

app.py
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import logging
import json
from io import BytesIO
from pyhprof.parser import HprofParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load microservices configuration
with open('microservices_config.json', 'r') as f:
    microservices_config = json.load(f)

# Initialize FastAPI app
app = FastAPI()

class AnalysisRequest(BaseModel):
    service_name: str
    prompt: str

@app.post("/analyze/")
async def analyze(service_name: str = Form(...), prompt: str = Form(...), hprof_file: UploadFile = None):
    logger.info(f"Received analysis request for service: {service_name}")

    # Validate service name
    if service_name not in microservices_config:
        logger.error(f"Service {service_name} not found in configuration.")
        raise HTTPException(status_code=404, detail="Service not found")

    # Process Hprof file if provided
    if hprof_file:
        logger.info(f"Processing Hprof file: {hprof_file.filename}")
        hprof_content = await hprof_file.read()
        hprof_analysis = analyze_hprof(hprof_content)
    else:
        hprof_analysis = "No Hprof file provided."

    # Generate AI response
    ai_response = generate_ai_response(prompt, hprof_analysis)

    return JSONResponse(content={"analysis": ai_response})

def analyze_hprof(hprof_content: bytes) -> str:
    try:
        # Parse Hprof content from bytes
        hprof_stream = BytesIO(hprof_content)
        parser = HprofParser(hprof_stream)
        heap = parser.parse()

        # Example: Analyze heap data (customize as needed)
        num_classes = len(heap.classes)
        num_instances = sum(len(cls.instances) for cls in heap.classes.values())

        analysis_result = f"Classes Found: {num_classes}, Instances Found: {num_instances}"

        # Additional analysis can be added here

        return analysis_result

    except Exception as e:
        logger.error(f"Error parsing Hprof file: {str(e)}")
        return "Error analyzing Hprof file."

def generate_ai_response(prompt: str, hprof_analysis: str) -> str:
    # Combine prompt and Hprof analysis
    combined_input = f"{prompt}\n\nHprof Analysis:\n{hprof_analysis}"
    # Placeholder for AI model integration
    # Replace this with actual AI model inference code
    response = f"AI Response based on input: {combined_input}"
    return response



------

project-root/
│
├── backend/
│   ├── app.py
│   └── microservices_config.json
│
└── frontend/
    ├── public/
    │   └── models/
    │       └── upload_animation.glb
    ├── pages/
    │   ├── _app.js
    │   ├── index.js
    │   └── api/
    │       └── analyze.js
    ├── components/
    │   ├── FileUpload.js
    │   ├── PromptInput.js
    │   └── ServiceSelector.js
    ├── styles/
    │   └── globals.css
    ├── next.config.js
    └── package.json




  ---


  Backend Setup
1. microservices_config.json:


{
    "serviceA": "https://github.com/your-org/serviceA-repo",
    "serviceB": "https://github.com/your-org/serviceB-repo"
}


----



{
  "services": {
    "Service-Aa": {
      "repo_url": "https://stash.company.com/projects/PROJ/repos/service-aa",
      "requires_token": true,
      "auth_type": "token",
      "token": "YOUR_TOKEN_HERE"
    },
    "Service-Ab": {
      "repo_url": "https://stash.company.com/projects/PROJ/repos/service-ab",
      "requires_token": false,
      "auth_type": "basic",
      "username": "user",
      "password": "pass"
    },
    "Service-Ac": {
      "repo_url": "https://stash.company.com/projects/PROJ/repos/service-ac",
      "requires_token": true,
      "auth_type": "token",
      "token": "ANOTHER_TOKEN"
    }
  },
  "default_headers": {
    "Accept": "application/json"
  }
}



import io
import json
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from typing import Optional

app = FastAPI()

# Initialize logging
logging.basicConfig(
    filename='backend.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load service configuration
try:
    with open('config.json') as config_file:
        config = json.load(config_file)
        logger.info("Service configuration loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load service configuration: {e}")
    config = {}

# Pydantic model for code analysis request
class CodeAnalysisRequest(BaseModel):
    service_name: str
    prompt: str

# Endpoint to upload and analyze Hprof file
@app.post("/upload_hprof/")
async def upload_hprof(file: UploadFile = File(...)):
    try:
        content = await file.read()
        logger.info(f"Received Hprof file: {file.filename}")
        analysis_result = analyze_hprof(content)
        return JSONResponse(content={"analysis_result": analysis_result}, status_code=200)
    except Exception as e:
        logger.error(f"Error processing Hprof file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Hprof file.")

# Endpoint to analyze code based on service name and prompt
@app.post("/analyze_code/")
async def analyze_code(request: CodeAnalysisRequest):
    try:
        service_info = config.get("services", {}).get(request.service_name)
        if not service_info:
            logger.warning(f"Service '{request.service_name}' not found in configuration.")
            raise HTTPException(status_code=404, detail="Service not found.")

        repo_url = service_info.get("repo_url")
        auth_type = service_info.get("auth_type")
        headers = config.get("default_headers", {})

        if auth_type == "token":
            token = service_info.get("token")
            headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "basic":
            username = service_info.get("username")
            password = service_info.get("password")
            auth = (username, password)
        else:
            auth = None

        logger.info(f"Fetching code from repository: {repo_url}")
        response = requests.get(repo_url, headers=headers, auth=auth)
        if response.status_code != 200:
            logger.error(f"Failed to fetch code from repository: {response.status_code}")
            raise HTTPException(status_code=500, detail="Failed to fetch code from repository.")

        code_content = response.text
        analysis_result = analyze_code_with_prompt(code_content, request.prompt)
        return JSONResponse(content={"analysis": analysis_result}, status_code=200)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error during code analysis: {e}")
        raise HTTPException(status_code=500, detail="Code analysis failed.")

# Health check endpoint
@app.get("/")
async def read_root():
    return {"status": "Backend is running."}

# Placeholder function to analyze Hprof content
def analyze_hprof(content: bytes) -> str:
    # Implement your Hprof analysis logic here
    logger.debug("Analyzing Hprof content.")
    return "Hprof analysis result."

# Placeholder function to analyze code with a given prompt
def analyze_code_with_prompt(code: str, prompt: str) -> str:
    # Implement your code analysis logic here
    logger.debug("Analyzing code with prompt.")
    return f"Analysis based on prompt '{prompt}': Code analysis result."




pip install fastapi uvicorn pydantic torch requests python-json-logger

pip install torch sentencepiece


pip install torch sentencepiece


/backend
 ┣ app.py               # Your all-in-one FastAPI backend
 ┣ config.json          # Mapping microservices → Stash repos
 ┣ /hprof_files         # Store uploaded hprof files
 ┣ llama_model/         # Your llama-2-7b files
 ┗ logs.log             # Log file


   uvicorn app:app --reload


   

/frontend
 ┣ /components
 ┃ ┣ ServiceTree.js
 ┃ ┗ ResultDisplay.js
 ┣ /pages
 ┃ ┗ index.js
 ┣ /public
 ┃ ┗ placeholder.png
 ┣ /styles
 ┃ ┗ globals.css
 ┗ next.config.js

/components/ServiceTree.js

import React from 'react';
import { Tree } from 'react-d3-tree';

const treeData = {
  name: 'MainApp',
  children: [
    { name: 'Service-Aa' },
    { name: 'Service-Ab' },
    { name: 'Service-Ac' },
  ],
};

export default function ServiceTree({ onSelect }) {
  const handleClick = (nodeData) => {
    if (!nodeData.children) {
      onSelect(nodeData.name);
    }
  };

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <Tree
        data={treeData}
        orientation="horizontal"
        onNodeClick={handleClick}
        translate={{ x: 100, y: 150 }}
        styles={{
          links: { stroke: '#888' },
          nodes: { node: { circle: { fill: '#00bfa5' } } },
        }}
      />
    </div>
  );
}

-----

/components/ResultDisplay.js

import React from 'react';

export default function ResultDisplay({ result }) {
  return (
    <div className="p-4 bg-gray-100 rounded-xl shadow">
      <h2 className="text-lg font-bold mb-2">Analysis Result:</h2>
      <pre className="whitespace-pre-wrap text-sm">{result}</pre>
    </div>
  );
}


------

/pages/index.js

import { useState } from 'react';
import ServiceTree from '../components/ServiceTree';
import ResultDisplay from '../components/ResultDisplay';

export default function Home() {
  const [service, setService] = useState('');
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState('');

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleAnalyze = async () => {
    const formData = new FormData();
    formData.append('file', file);

    const hprofResponse = await fetch('http://localhost:8000/upload_hprof/', {
      method: 'POST',
      body: formData,
    });
    const hprofData = await hprofResponse.json();

    const codeResponse = await fetch('http://localhost:8000/analyze_code/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ service_name: service, prompt }),
    });
    const codeData = await codeResponse.json();

    setResult(`HPROF Result: ${hprofData.analysis_result}\n\nCode Analysis:\n${codeData.analysis}`);
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">AI Code & Hprof Analyzer</h1>
      <ServiceTree onSelect={setService} />
      <p className="mt-2 mb-4">Selected Service: <strong>{service || 'None'}</strong></p>

      <input
        type="file"
        className="mb-4"
        onChange={handleFileChange}
      />

      <textarea
        className="w-full mb-4 p-2 border rounded"
        rows="4"
        placeholder="Enter your analysis prompt..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />

      <button
        onClick={handleAnalyze}
        disabled={!service || !file || !prompt}
        className="bg-blue-600 text-white px-4 py-2 rounded"
      >
        Analyze
      </button>

      {result && <ResultDisplay result={result} />}
    </div>
  );
}



----
/styles/globals.css

@tailwind base;
@tailwind components;
@tailwind utilities;

----

next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

module.exports = nextConfig;


----


npm install react-d3-tree tailwindcss
npx tailwindcss init

----
cd frontend
npm run dev



import os
import logging
from logging.config import dictConfig
from typing import List, Optional
from fastapi import FastAPI, UploadFile, Form, HTTPException
from pydantic import BaseModel
import torch
from transformers import LlamaForCausalLM, LlamaTokenizer
import requests
from io import BytesIO
import zipfile
import tempfile

# Logging Configuration
def setup_logging():
    log_config = {
        "version": 1,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }
    dictConfig(log_config)

setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Model Loading Function
def load_llama_model(model_dir: str):
    try:
        logger.info(f"Loading model from {model_dir}")
        tokenizer = LlamaTokenizer.from_pretrained(model_dir)
        model = LlamaForCausalLM.from_pretrained(
            model_dir,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        logger.info("Model loaded successfully.")
        return tokenizer, model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

# Load the model at startup
MODEL_DIR = "/path/to/your/open_llama-2-7b"
tokenizer, model = load_llama_model(MODEL_DIR)

# HPROF Analysis Function
def analyze_hprof(file_path: str) -> str:
    try:
        logger.info(f"Analyzing HPROF file: {file_path}")
        # Placeholder for HPROF analysis logic
        analysis_result = "Memory leak detected in com.example.MyClass"
        logger.info(f"HPROF analysis completed: {analysis_result}")
        return analysis_result
    except Exception as e:
        logger.error(f"Error analyzing HPROF file: {e}")
        raise

# Stash Code Retrieval Function
def retrieve_code_from_stash(repo_url: str, service_name: str) -> str:
    try:
        logger.info(f"Retrieving code from Stash repository: {repo_url} for service: {service_name}")
        # Placeholder for code retrieval logic
        code_snippet = "public class MyClass { ... }"
        logger.info(f"Code retrieval successful for service: {service_name}")
        return code_snippet
    except Exception as e:
        logger.error(f"Error retrieving code from Stash: {e}")
        raise

# Request Models
class AnalysisRequest(BaseModel):
    service_name: str
    prompt: str

# FastAPI Endpoints
@app.post("/upload_hprof/")
async def upload_hprof(file: UploadFile):
    try:
        logger.info(f"Received HPROF file: {file.filename}")
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        analysis_result = analyze_hprof(file_path)
        return {"analysis_result": analysis_result}
    except Exception as e:
        logger.error(f"Error in upload_hprof endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/analyze_code/")
async def analyze_code(request: AnalysisRequest):
    try:
        logger.info(f"Analyzing code for service: {request.service_name}")
        code_snippet = retrieve_code_from_stash("https://stash.example.com/repo", request.service_name)
        inputs = tokenizer(request.prompt + code_snippet, return_tensors="pt").to("cuda")
        outputs = model.generate(**inputs)
        analysis = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Code analysis completed for service: {request.service_name}")
        return {"analysis": analysis}
    except Exception as e:
        logger.error(f"Error in analyze_code endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Main function to run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
