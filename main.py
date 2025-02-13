import json
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import pdfplumber
from io import BytesIO
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI and logger
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv(".env")
GEMINI_API_KEY = os.getenv("GEMINI_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing Google Gemini API key. Set GEMINI_KEY in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# Thread pool for PDF processing
executor = ThreadPoolExecutor(2)
loop = asyncio.get_event_loop()


def extract_text_from_pdf(file: BytesIO) -> str:
    """Extracts text from a PDF file."""
    with pdfplumber.open(file) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()


def extract_json_from_text(text: str) -> dict:
    """
    Extracts the first valid JSON object from a given text string.

    Handles cases where Gemini returns surrounding text before or after the JSON response.
    """
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)  # Extract JSON enclosed in `{}`.
        if match:
            return json.loads(match.group(0))  # Convert string to dictionary.
    except json.JSONDecodeError as e:
        logger.error("JSON Parsing Error: %s", str(e))
    return {"error": "Failed to parse valid JSON from response."}


def analyze_resume_with_gemini(resume_md: str, job_description: str, specs: str, reqs: str) -> dict:
    """Uses Google Gemini to compare the resume against a job description and return JSON."""
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    You are an AI performing resume screening in a professional HR setting.

    Please follow these guidelines strictly:

    1. **Match Score**: Provide a match score between 0 and 100. This score should reflect how well the qualifications listed in the resume align with the job description, specifications, and requirements.
       - Base the score solely on the match between the resume and the job's core requirements.

    2. **Strengths**: List key strengths and relevant experience that align with the job description and requirements.
       - Provide strengths as bullet points.
       - Ensure strengths focus on specific skills and experience directly related to the job specifications and requirements.

    3. **Gaps/Weaknesses**: List any weaknesses or missing skills/experience in relation to the job specifications and requirements. If any key qualifications are missing, express them as **weaknesses** or **shortcomings**.
       - **Explicitly stating what is lacking** (e.g., missing skills, qualifications, or experience).
       - Avoid listing components as "missing" without framing them as **shortcomings** or **weaknesses**. For example:
       - If the resume lacks experience with a required technology, state: "Missing experience with [Technology], which is required for this role."
       - If a required skill is not found, express it as: "Lacks proficiency in [Skill], which is a key requirement."
       
    4. **Exclusion of Irrelevant Information**: Ignore any other details of the resume that are not directly related to the job description, specifications, or requirements.
       - Do not mention personal traits, preferences, or irrelevant experiences.

    The evaluation should be **objective, factual**, and **professional**. Avoid subjective language or personal opinions. Your responses should be based only on the **objective match** between the resume and job specifications.

    Evaluate the qualifications and experience based on the following:

    --- INPUT ---
    **Resume:**
    {resume_md}

    **Job Description:**
    {job_description}

    **Specifications:**
    {specs}

    **Requirements:**
    {reqs}

    Return **ONLY JSON** in this exact format:
    {{
        "match_score": <numeric_score_out_of_100>,
        "strengths": "<brief summary in bullet points>",
        "gaps": "<brief weaknesses in bullet points>"
    }}

    """


    try:
        response = model.generate_content(prompt)
        logger.info("Gemini Response: %s", response.text)

        # Extract valid JSON from the response
        return extract_json_from_text(response.text.strip())

    except Exception as e:
        logger.error("Gemini API Error: %s", str(e))
        return {"error": str(e)}

@app.post("/process_resume/")
async def process_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    specs: str = Form(...),
    reqs: str = Form(...),
):
    """Processes resume, extracts text, and sends it to Gemini."""
    try:
        file_content = await file.read()
        pdf_text = await loop.run_in_executor(executor, extract_text_from_pdf, BytesIO(file_content))
        analysis_result = analyze_resume_with_gemini(pdf_text, job_description, specs, reqs)
        return analysis_result
    except Exception as e:
        logger.error("Unexpected Error: %s", str(e))
        raise HTTPException(status_code=500, detail={"error": str(e)})


# Custom Exception Handler for Form Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    logger.error(f"Validation Error: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})