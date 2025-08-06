from daegon.shared import (KAFKA_CONFIG, SCHEMA_REGISTRY, MEMORY_TOPICS, 
                           ENCODING_SCHEMAS_FOLDER, MEMORY_SCHEMAS_FOLDER,
                           ECHO_TOPICS, ECHO_SCHEMAS_FOLDER, 
                           TEXTUAL_TOPICS, TEXTUAL_SCHEMAS_FOLDER)
from daegon.textualAnalysis import TEXTUAL_OLLAMA_SERVICE
from daegon.memory import FILESYSTEM_SERVICE
from daegon.utils import ECHO_SERVICE
from daegon.dsl.engine import DaegonDslEngine, Service
from daegon.shared.microservice import MicroserviceSettings
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List
import threading
import PyPDF2
import os
import io

# Initialize the DAEGON DSL engine with the necessary settings
settings = MicroserviceSettings(
        KAFKA_CONFIG,
        SCHEMA_REGISTRY,
        "group",
        ECHO_TOPICS + TEXTUAL_TOPICS + MEMORY_TOPICS,
        ECHO_SCHEMAS_FOLDER,
        "dsl-test",
        "test-layer"
    )

settings.schemas_folder = {
    "history": ENCODING_SCHEMAS_FOLDER,
    "memory": MEMORY_SCHEMAS_FOLDER,
    "echo": ECHO_SCHEMAS_FOLDER,
    "textual": TEXTUAL_SCHEMAS_FOLDER
}

engine = DaegonDslEngine(settings)

echo_req = os.path.join(ECHO_SCHEMAS_FOLDER, "echo_request.json")
echo_resp = os.path.join(ECHO_SCHEMAS_FOLDER, "echo_response.json")
text_prompt_req = os.path.join(TEXTUAL_SCHEMAS_FOLDER, "textual_prompt_request_v1.json")
text_prompt_resp = os.path.join(TEXTUAL_SCHEMAS_FOLDER, "textual_prompt_response_v1.json")
text_add_skill_req = os.path.join(TEXTUAL_SCHEMAS_FOLDER, "textual_add_skill_request_v1.json")
text_add_skill_resp = os.path.join(TEXTUAL_SCHEMAS_FOLDER, "textual_add_skill_response_v1.json")
memory_create_req = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_create_request_v1.json")
memory_create_resp = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_create_response_v1.json")
memory_retrieve_req = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_retrieve_by_id_request_v1.json")
memory_retrieve_resp = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_retrieve_by_id_response_v1.json")
memory_retrieve_similar_req = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_retrieve_similar_request_v1.json")
memory_retrieve_similar_resp = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_retrieve_similar_response_v1.json")
memory_update_req = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_update_request_v1.json")
memory_update_resp = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_update_response_v1.json")
memory_delete_req = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_delete_request_v1.json")
memory_delete_resp = os.path.join(MEMORY_SCHEMAS_FOLDER, "memory_delete_response_v1.json")

echo_service = ECHO_SERVICE
ollam_prompt_service = TEXTUAL_OLLAMA_SERVICE + "-prompt"
ollama_add_skill_service = TEXTUAL_OLLAMA_SERVICE + "-add-skill"
memory_create_service = FILESYSTEM_SERVICE + "-create"
memory_retrieve_service = FILESYSTEM_SERVICE + "-retrieve-by-id"
memory_retrieve_similar_service = FILESYSTEM_SERVICE + "-retrieve-similar"
memory_update_service = FILESYSTEM_SERVICE + "-update"
memory_delete_service = FILESYSTEM_SERVICE + "-delete"

engine.register_service(Service(echo_service, "echo-request", echo_req))
engine.register_service(Service(ollam_prompt_service, "textual-prompt-request", text_prompt_req))
engine.register_service(Service(ollama_add_skill_service, "textual-add-skill-request", text_add_skill_req))
engine.register_service(Service(memory_create_service, "memory-create-request", memory_create_req))
engine.register_service(Service(memory_retrieve_service, "memory-retrieve-by-id-request", memory_retrieve_req))
engine.register_service(Service(memory_retrieve_similar_service, "memory-retrieve-similar-request", memory_retrieve_similar_req))
engine.register_service(Service(memory_update_service, "memory-update-request", memory_update_req))
engine.register_service(Service(memory_delete_service, "memory-delete-request", memory_delete_req))

# First rest service EVER TESTED IN DAEGON!
world_time_service = Service(
    name="worldtime",
    address="https://timeapi.io/api/time/current/zone?timeZone=Europe%2FAmsterdam",
    schema_path="",
    protocol="rest",
    method="GET",
    timeout=5
)
engine.register_service(world_time_service)

engine.register_schema(echo_req, "echo_request")
engine.register_schema(echo_resp, "echo_response")
engine.register_schema(text_prompt_req, "textual_prompt_request_v1")
engine.register_schema(text_prompt_resp, "textual_prompt_response_v1")
engine.register_schema(text_add_skill_req, "textual_add_skill_request_v1")
engine.register_schema(text_add_skill_resp, "textual_add_skill_response_v1")
engine.register_schema(memory_create_req, "memory_create_request_v1")
engine.register_schema(memory_create_resp, "memory_create_response_v1")
engine.register_schema(memory_retrieve_req, "memory_retrieve_by_id_request_v1")
engine.register_schema(memory_retrieve_resp, "memory_retrieve_by_id_response_v1")
engine.register_schema(memory_retrieve_similar_req, "memory_retrieve_similar_request_v1")
engine.register_schema(memory_retrieve_similar_resp, "memory_retrieve_similar_response_v1")
engine.register_schema(memory_update_req, "memory_update_request_v1")
engine.register_schema(memory_update_resp, "memory_update_response_v1")
engine.register_schema(memory_delete_req, "memory_delete_request_v1")
engine.register_schema(memory_delete_resp, "memory_delete_response_v1")

full_chat_script = """
workflow optimized_full_chat_workflow {
    steps {
        initialize_history: call file-system-memory-create with {
            {
                "eventType": "memory.create.request",
                "memoryId": "chat-history",
                "namespace": "chat",
                "document": encode("<INIT>"),
                "mimeType": "text/plain",
                "overwrite": false,
                "metadata": {
                    "target": "file-system-memory",
                    "source": "dsl-test",
                    "sourceType": "user_type",
                    "timestamp": 1700000000 
                }
            }
        }
        get_full_history: call file-system-memory-retrieve-by-id with {
            {
                "eventType": "memory.retrieve-by-id.request",
                "memoryId": "chat-history",
                "namespace": "chat",
                "metadata": {
                    "target": "file-system-memory",
                    "source": "dsl-test",
                    "sourceType": "user_type",
                    "timestamp": 1700000000
                }
            }
        }
        ollama_add_skill: call ollama-textual-add-skill with {
            {
                "eventType": "textual.add_skill",
                "skillUrl": "SemanticSkills/main/Skills",
                "skillLocation": "MiscSkill",
                "skillName": "empty",
                "metadata": {
                    "target": "ollama-textual",
                    "source": "dsl-test",
                    "sourceType": "user_type",
                    "timestamp": 1700000000
                }
            }
        }
        ollama_prompt: call ollama-textual-prompt with {
            {
                "eventType": "textual.prompt.request",
                "prompt": {
                    "input": concat(
                        str($get_full_history.result.memory),
                        nl(),
                        "<USER> %(user_message)s"
                    )
                },
                "skillName": "empty",
                "metadata": {
                    "target": "ollama-textual",
                    "source": "dsl-test",
                    "sourceType": "user_type",
                    "timestamp": 1700000000
                }
            }
        }
        update_chat_history: call file-system-memory-create with {
            {
                "eventType": "memory.update.request",
                "namespace": "chat",
                "memoryId": "chat-history",
                "document": encode(
                    str(
                        concat(
                            str($get_full_history.result.memory),
                            nl(),
                            "<USER> %(user_message)s",
                            nl(),
                            "<BOT> ", first($ollama_prompt.result.modelResponses)
                        )
                    )
                ),
                "mimeType": "text/plain",
                "overwrite": true,
                "metadata": {
                    "target": "file-system-memory",
                    "source": "dsl-test",
                    "sourceType": "user_type",
                    "timestamp": 1700000000
                }
            }
        }
    }
    output {
        response: first($ollama_prompt.result.modelResponses)
    }
}
"""

file_upload_workflow = """ 
workflow file_upload_workflow {
    steps {
        file_upload: call file-system-memory-create with {
            {
                "eventType": "memory.create.request",
                "memoryId": "%(chunk_id)s",
                "namespace": "file_uploads",
                "document": encode("%(chunk_text)s"),
                "mimeType": "text/plain",
                "overwrite": false,
                "metadata": {
                    "target": "file-system-memory",
                    "source": "dsl-test",
                    "sourceType": "user_type",
                    "timestamp": 1700000000
                }
            }
        }
    }
    output {
        status: $file_upload.result.status
    }
}
"""

def extract_text_from_pdf(pdf_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    full_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"
    return full_text

def split_into_paragraphs(text):
    # This splits by periods followed by a newline, or just double newlines
    import re
    # First, normalize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Break paragraphs by two or more newlines
    paragraphs = re.split(r'\n{2,}', text)
    # Optionally, further split any paragraph on periods followed by newline
    chunks = []
    for p in paragraphs:
        # Avoid empty
        p = p.strip()
        if not p:
            continue
        splitted = re.split(r'\.\s*\n', p)
        for part in splitted:
            part = part.strip()
            if part:
                chunks.append(part)
    return chunks

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class FileUploadResponse(BaseModel):
    chunk_ids: list[str]
    total_chunks: int
    failure_ids: list[str] = []
    failure_chunks: list[str] = []
    failure_count: int = 0

# --- FastAPI Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    listener_thread = threading.Thread(target=engine.listen)
    listener_thread.daemon = True
    listener_thread.start()
    yield

app = FastAPI(title="DAEGON Chat API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the DAEGON Chat API. Use /chat to send messages."}

@app.get("/workflow")
async def get_workflow():
    return {"workflow": full_chat_script}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    chunk_ready = threading.Event()
    result_holder = {}
    failures = []
    def on_completed(result):
       status: str = result.get("status").get("code", "unknown")
       if status.lower() != "success":
           metadata: dict = result.get("metadata", {})
           correlation_id: str = metadata.get("correlationId", "unknown")
           print(f"Workflow completed with status: {status}, correlationId: {correlation_id}")
           raise HTTPException(status_code=500, detail=f"Workflow failed with status: {status}, correlationId: {correlation_id}")
    
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files supported.")
    try:
        content = await file.read()
        text = extract_text_from_pdf(content)
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF.")
        chunks: List[str] = split_into_paragraphs(text)
        for chunk in chunks:
            chunk_text: str = str(chunk).strip()
            if not chunk_text:
                continue
            chunk_id = f"chunk-{hash(chunk_text)}"
            chunk_text = chunk_text.replace('"', "'")  # Replace double quotes with single quotes
            chunk_script = file_upload_workflow % {"chunk_id": chunk_id, "chunk_text": chunk_text}
            evaluator_id, evaluator = engine.create_evaluator(chunk_script)
            evaluator.set_on_completed_execution(on_completed)
            evaluator.start()
            chunk_ready.wait(timeout=60)  # 60-second max wait
            result = result_holder.get("result")
            if not result or "status" not in result or result["status"]["code"] != "success":
                failures.append((chunk_id, chunk_text))
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    
    return FileUploadResponse(
        chunk_ids=[f"chunk-{hash(chunk)}" for chunk in chunks],
        total_chunks=len(chunks),
        failure_ids=[f"chunk-{hash(chunk)}" for chunk, _ in failures],
        failure_chunks=[chunk for _, chunk in failures],
        failure_count=len(failures)
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_message = request.message.strip().replace('"', "'")  # Replace double quotes with single quotes for safety
    if not user_message:
        raise HTTPException(status_code=400, detail="Message must not be empty.")

    # Generate full DSL script for this turn
    chat_script = full_chat_script % {"user_message": user_message}
    evaluator_id, evaluator = engine.create_evaluator(chat_script)

    # Use an event to signal workflow completion, since evaluation is async
    import threading
    chat_ready = threading.Event()
    result_holder = {}

    def on_completed(result):
        result_holder["result"] = result
        chat_ready.set()

    evaluator.set_on_completed_execution(on_completed)
    evaluator.start()
    chat_ready.wait(timeout=60)  # 60-second max wait

    # Parse result
    result = result_holder.get("result")
    if not result or "response" not in result or not isinstance(result["response"], str):
        raise HTTPException(status_code=500, detail="No response available or workflow error.")

    return ChatResponse(response=result["response"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)