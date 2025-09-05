from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import os
import shutil
import uuid
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import models  
import database  
from matcher import match_resume_to_jobs  


# Create DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobIn(BaseModel):
    title: str
    skills_required: List[str]

class ResumeIn(BaseModel):
    name: str
    skills: List[str]


@app.post("/add-job")
def add_job(
    title: str = Form(...),
    description: str = Form(...),
    skills: str = Form(...),  # Comma separated string
    location: str = Form(...),
    education_requirements: str = Form(...),
    eligibility_criteria: str = Form(...)
):
    db = database.SessionLocal()
    job = models.Job(
        title=title,
        description=description,
        skills=skills,
        location=location,
        education_requirements=education_requirements,
        eligibility_criteria=eligibility_criteria,
    )
    db.add(job)
    db.commit()
    db.close()
    return {"message": "Job added successfully"}


@app.post("/upload-resume")
def upload_resume_file(
    name: str = Form(...),
    skills: List[str] = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files allowed.")

    os.makedirs("uploaded_resumes", exist_ok=True)

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"uploaded_resumes/{unique_filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db = database.SessionLocal()
    db_resume = models.Resume(
        name=name,
        skills=",".join(skills),
        file_path=file_path
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    db.close()

    return {"message": "Resume uploaded", "file": unique_filename}


@app.delete("/clear-jobs")
def clear_jobs():
    db = database.SessionLocal()
    deleted = db.query(models.Job).delete()
    db.commit()
    db.close()
    return {"message": f"Deleted {deleted} jobs"}


@app.delete("/clear-resumes")
def clear_resumes():
    db = database.SessionLocal()

    # Delete stored files
    resumes = db.query(models.Resume).all()
    for resume in resumes:
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)

    deleted = db.query(models.Resume).delete()
    db.commit()
    db.close()
    return {"message": f"Deleted {deleted} resumes and files"}


@app.get("/match")
def match_resume():
    results = match_resume_to_jobs()
    if not results:
        raise HTTPException(status_code=404, detail="No matches found.")

    return results if isinstance(results, dict) else {"matches": results}
