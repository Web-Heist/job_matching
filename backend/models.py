from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text
Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    skills = Column(Text)
    location = Column(String)
    education_requirements = Column(Text)
    eligibility_criteria = Column(Text)

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    skills = Column(Text)
    education = Column(Text)
    experience = Column(Text)
    file_path = Column(String)  # new field
