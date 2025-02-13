
# Resume Analyzer

## Overview
This project evaluates resumes by comparing them against a job description. It extracts key insights, highlights strengths, and identifies gaps using **FastAPI** and **Google Gemini API**.

## Features
✅ Accepts PDF resumes for analysis  
✅ Compares resumes against job descriptions  
✅ Provides structured results (match score, strengths, weaknesses)  
✅ Simple web frontend for easy interaction  

## Tech Stack
- **Backend:** FastAPI, Google Gemini API  
- **Sample Frontend:** HTML, JavaScript, CSS  

---

## 🚀 Setup Guide  

### 1️⃣ Clone the Repository  

Run in terminal
git clone https://github.com/yourusername/resume-analyzer.git
cd parse-res

python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

## Fetch requirements via pip
pip install -r requirements.txt 

## Setup environment secrets (Gemini key)
Create a .env file in the root directory and add:
GEMINI_API_KEY=your_api_key_here

##  Run the Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

## Frontend startup
Open index.html in the browser to startup the frontend


The app is now ready to experiment and test.
Could not deploy it because backend hosting needed more time to setup.
 
!! Please note:
Gemini sometimes returns outputs without json, which are not accessible to the frontend. Just resubmit the input, the next response will likely be properly serializable
Potential fix: set temperature=0 in Gemini Params, did not get time to experiment and confirm.