import os
import docx2txt
import pdfplumber
from fuzzywuzzy import fuzz
from models import Job, Resume
from database import SessionLocal
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure Gemini
genai.configure(api_key="AIzaSyBuKUqZFRiMcTekS-NRLDJnkEjFPDuMqI4")
model = genai.GenerativeModel(model_name="gemini-2.5-pro")

# Extract text from PDF or DOCX
def extract_text_from_file(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    elif file_path.endswith(".docx"):
        return docx2txt.process(file_path)
    else:
        return ""

# Get Gemini score
def get_gemini_match_score(job_text: str, resume_text: str) -> float:
    prompt = f"""
    Job Description:
    {job_text}

    Resume:
    {resume_text}

    Based on the resume and the job description, give a match score out of 10 (just the number) indicating how suitable the candidate is for this job.
    """
    try:
        response = model.generate_content(prompt)
        score = response.text.strip()
        return float(score) if score.replace(".", "", 1).isdigit() else 0
    except Exception as e:
        print("Gemini error:", e)
        return 0

# Matching function for a single job-resume pair
def compute_job_score(job, resume_text, resume_skills, resume_name):
    job_skills = set(skill.strip().lower() for skill in job.skills.split(",") if skill.strip())
    score = 0

    # Fuzzy skill matching
    for r_skill in resume_skills:
        for j_skill in job_skills:
            if fuzz.partial_ratio(r_skill, j_skill) > 40:
                score += 3

    # Additional fuzzy matching
    score += fuzz.partial_ratio(job.title.lower(), resume_text) // 6 if job.title else 0
    score += fuzz.partial_ratio(job.description.lower(), resume_text) // 15 if job.description else 0

    if job.education_requirements:
        if fuzz.partial_ratio(job.education_requirements.lower(), resume_text) > 75:
            score += 2

    if job.eligibility_criteria and "year" in job.eligibility_criteria.lower():
        if fuzz.partial_ratio(job.eligibility_criteria.lower(), resume_text) > 75:
            score += 5

    if job.location:
        if fuzz.partial_ratio(job.location.lower(), resume_text) > 70:
            score += 1

    job_text = f"{job.title}\n{job.description}\n{job.education_requirements or ''}\n{job.eligibility_criteria or ''}\n{job.location or ''}"
    gemini_score = get_gemini_match_score(job_text, resume_text)

    combined_score = score + (gemini_score * 2)

    print(f"  Job: {job.title}, Keyword Score:{score}, Gemini Score: {gemini_score}, Combined Score: {combined_score}")

    return {
        "resume_name": resume_name,
        "matched_job_title": job.title,
        "job_description":job.description,
        "job_skills":job.skills,
        "match_score": combined_score,
        "job_location": job.location,
        "education_requirements": job.education_requirements,
        "eligibility_criteria": job.eligibility_criteria
    }

# Main function with parallel processing
def match_resume_to_jobs():
    db = SessionLocal()
    resumes = db.query(Resume).all()
    jobs = db.query(Job).all()
    top_matches = []

    for resume in resumes:
        resume_text = extract_text_from_file(resume.file_path).lower()
        if not resume_text.strip():
            continue

        resume_skills = set(skill.strip().lower() for skill in resume.skills.split(",") if skill.strip())
        job_scores = []

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(compute_job_score, job, resume_text, resume_skills, resume.name)
                for job in jobs
            ]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    job_scores.append(result)

        # Sort and get top 3
        top_3 = sorted(job_scores, key=lambda x: x["match_score"], reverse=True)[:3]
        top_matches.extend(top_3)

    db.close()
    return top_matches
