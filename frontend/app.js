const skills = [
  ["python", "Python"],
  ["java", "Java"],
  ["cpp", "C++"],
  ["javascript", "JavaScript"],
  ["html", "HTML"],
  ["css", "CSS"],
  ["react", "React"],
  ["nodejs", "Node.js"],
  ["fastapi", "FastAPI"],
  ["sql", "SQL"],
  ["mysql", "MySQL"],
  ["mongodb", "MongoDB"],
  ["git", "Git"],
  ["github", "GitHub"],
  ["linux", "Linux"],
  ["docker", "Docker"],
  ["aws", "AWS"],
  ["machine_learning", "Machine Learning"],
  ["deep_learning", "Deep Learning"],
  ["data_analysis", "Data Analysis"],
  ["power_bi", "Power BI"],
  ["tableau", "Tableau"],
  ["excel", "Excel"],
  ["communication", "Communication"],
  ["problem_solving", "Problem Solving"],
  ["teamwork", "Teamwork"],
  ["critical_thinking", "Critical Thinking"],
];

const interests = [
  ["ai", "AI"],
  ["data_science", "Data Science"],
  ["web_development", "Web Development"],
  ["mobile_development", "Mobile Development"],
  ["cloud", "Cloud"],
  ["devops", "DevOps"],
  ["cybersecurity", "Cybersecurity"],
  ["finance", "Finance"],
  ["research", "Research"],
];

const defaultSkills = new Set(["python", "sql", "machine_learning", "data_analysis", "git", "communication"]);
const defaultInterests = new Set(["ai", "data_science"]);

function renderCheckboxes(containerId, values, selectedValues) {
  const container = document.getElementById(containerId);
  container.innerHTML = values
    .map(([value, label]) => {
      const checked = selectedValues.has(value) ? "checked" : "";
      return `
        <label class="chip">
          <input type="checkbox" value="${value}" ${checked} />
          <span>${label}</span>
        </label>
      `;
    })
    .join("");
}

function numberValue(formData, key) {
  const value = formData.get(key);
  return value === "" || value === null ? null : Number(value);
}

function selectedValues(containerId) {
  return Array.from(document.querySelectorAll(`#${containerId} input:checked`)).map((input) => input.value);
}

function confidencePercent(value) {
  return Math.round(Number(value) * 100);
}

function renderTags(values, emptyText) {
  if (!values.length) {
    return `<span class="tag">${emptyText}</span>`;
  }

  return values.map((value) => `<span class="tag">${value}</span>`).join("");
}

function renderRoadmap(steps) {
  return steps
    .map(
      (step) => `
        <div class="roadmap-step">
          <strong>${step.title}</strong>
          <ul>
            ${step.actions.map((action) => `<li>${action}</li>`).join("")}
          </ul>
        </div>
      `
    )
    .join("");
}

function renderRecommendations(recommendations) {
  const results = document.getElementById("results");
  const emptyState = document.getElementById("emptyState");

  emptyState.style.display = "none";
  results.innerHTML = recommendations
    .map((recommendation) => {
      const percent = confidencePercent(recommendation.confidence);
      return `
        <article class="career-card">
          <div class="career-topline">
            <div>
              <h3 class="career-title">${recommendation.career}</h3>
              <p class="muted">Career match based on your current profile</p>
            </div>
            <div class="confidence">${percent}%</div>
          </div>
          <div class="meter"><span style="width: ${percent}%"></span></div>
          <div class="skill-row">
            <div class="skill-box">
              <h4>Matched Skills</h4>
              <div class="tag-list">${renderTags(recommendation.matched_skills, "No direct match yet")}</div>
            </div>
            <div class="skill-box">
              <h4>Skills To Build</h4>
              <div class="tag-list">${renderTags(recommendation.missing_skills, "No major gap")}</div>
            </div>
          </div>
          <div class="roadmap">
            <h4>Roadmap</h4>
            ${renderRoadmap(recommendation.roadmap)}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderError(message) {
  document.getElementById("emptyState").style.display = "none";
  document.getElementById("results").innerHTML = `<div class="error-message">${message}</div>`;
}

async function checkApiStatus() {
  const status = document.getElementById("apiStatus");

  try {
    const response = await fetch("/api/health");
    if (!response.ok) {
      throw new Error("API unavailable");
    }
    status.textContent = "Ready";
    status.className = "status-pill ready";
  } catch {
    status.textContent = "Offline";
    status.className = "status-pill error";
  }
}

async function submitProfile(event) {
  event.preventDefault();

  const form = event.currentTarget;
  const button = document.getElementById("submitButton");
  const formData = new FormData(form);

  const payload = {
    education_level: formData.get("education_level"),
    branch: formData.get("branch"),
    specialization: formData.get("specialization"),
    cgpa: numberValue(formData, "cgpa"),
    class_10_percentage: numberValue(formData, "class_10_percentage"),
    class_12_percentage: numberValue(formData, "class_12_percentage"),
    total_certifications: numberValue(formData, "total_certifications") || 0,
    total_projects: numberValue(formData, "total_projects") || 0,
    internship_count: numberValue(formData, "internship_count") || 0,
    hackathons: numberValue(formData, "hackathons") || 0,
    leetcode_questions: numberValue(formData, "leetcode_questions") || 0,
    github_repositories: numberValue(formData, "github_repositories") || 0,
    expected_salary_lpa: numberValue(formData, "expected_salary_lpa"),
    preferred_work_mode: formData.get("preferred_work_mode"),
    career_goal: formData.get("career_goal"),
    skills: selectedValues("skillsGrid"),
    interests: selectedValues("interestsGrid"),
  };

  button.disabled = true;
  button.textContent = "Running Prediction";

  try {
    const response = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Recommendation failed");
    }

    renderRecommendations(data.recommendations);
  } catch (error) {
    renderError(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Recommend Careers";
  }
}

renderCheckboxes("skillsGrid", skills, defaultSkills);
renderCheckboxes("interestsGrid", interests, defaultInterests);
document.getElementById("profileForm").addEventListener("submit", submitProfile);
checkApiStatus();
