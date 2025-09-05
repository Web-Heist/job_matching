const jobForm = document.getElementById("job-form");
const resumeForm = document.getElementById("resume-form");
const resultsDiv = document.getElementById("results");
const clearResponse = document.getElementById("clear-response");

document.getElementById("job-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const formData = new FormData(this);

  const response = await fetch("http://localhost:8000/add-job", {
      method: "POST",
      body: formData
  });

  
  const result = await response.json();
  alert(result.message);
});

resumeForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(resumeForm);

  try {
    const res = await fetch("http://localhost:8000/upload-resume", {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error("Failed to upload resume");
    const data = await res.json();
    const matches = data.matches;
    alert("Resume uploaded!");
    console.log(data);
  } catch (err) {
    console.error("Error uploading resume:", err);
    alert("Error uploading resume.");
  }
});

async function clearJobs() {
  try {
    const res = await fetch("http://localhost:8000/clear-jobs", {
      method: "DELETE"
    });
    const data = await res.json();
    clearResponse.innerText = data.message;
  } catch (err) {
    console.error("Error clearing jobs:", err);
  }
}

async function clearResumes() {
  try {
    const res = await fetch("http://localhost:8000/clear-resumes", {
      method: "DELETE"
    });
    const data = await res.json();
    clearResponse.innerText = data.message;
  } catch (err) {
    console.error("Error clearing resumes:", err);
  }
}

async function loadMatches() {
  try {
    const res = await fetch("http://localhost:8000/match");
    if (!res.ok) {
      throw new Error("Failed to fetch matches");
    }

    const data = await res.json();
    const matches = data.matches;

    if (!Array.isArray(matches) || matches.length === 0) {
      resultsDiv.innerHTML = "<p>No matches found.</p>";
      return;
    }

    resultsDiv.innerHTML = "<h2>Matches</h2>";

    matches.forEach((match) => {
      const div = document.createElement("div");
      div.innerHTML = `
        <p><strong>Job:</strong> ${match.matched_job_title || "N/A"}</p>
        <p><strong>Candidate:</strong> ${match.resume_name || "N/A"}</p>
        <p><strong>Match Score:</strong> ${match.match_score ?? "N/A"}</p>
        <p><strong>Description:</strong> ${match.job_description ?? "N/A"}</p>
        <p><strong>Required Skills:</strong> ${match.job_skills?? "N/A"}</p>
        <p><strong>Location:</strong> ${match.job_location || "N/A"}</p>
        <p><strong>Requirements:</strong> ${match.education_requirements || "N/A"}</p>
        <p><strong>Eligibility:</strong> ${match.eligibility_criteria || "N/A"}</p>
        <hr>
      `;
      resultsDiv.appendChild(div);
    });

  } catch (err) {
    console.error("Error fetching matches:", err);
    resultsDiv.innerHTML = "<p>Error fetching matches.</p>";
  }
}
