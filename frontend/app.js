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
  ["pandas", "Pandas"],
  ["statistics", "Statistics"],
  ["machine_learning", "Machine Learning"],
  ["deep_learning", "Deep Learning"],
  ["computer_vision", "Computer Vision"],
  ["nlp", "NLP"],
  ["data_analysis", "Data Analysis"],
  ["power_bi", "Power BI"],
  ["tableau", "Tableau"],
  ["excel", "Excel"],
  ["networking", "Networking"],
  ["cybersecurity", "Cybersecurity"],
  ["blockchain", "Blockchain"],
  ["testing", "Testing"],
  ["automation", "Automation"],
  ["design", "Design"],
  ["figma", "Figma"],
  ["unity", "Unity"],
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
  ["game_development", "Game Development"],
  ["business_analytics", "Business Analytics"],
  ["design", "Design"],
];

const defaultSkills = new Set(["python", "sql", "machine_learning", "data_analysis", "git", "communication"]);
const defaultInterests = new Set(["ai", "data_science"]);
let lastProfile = null;
let lastRecommendations = [];
let chatHistory = [];

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

function listValue(formData, key) {
  const value = formData.get(key) || "";
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
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

function addChatBubble(role, content) {
  const container = document.getElementById("chatMessages");
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  bubble.textContent = content;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
  return bubble;
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
    certifications: listValue(formData, "certifications"),
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
    lastProfile = payload;
    lastRecommendations = data.recommendations;
    addChatBubble("assistant", `I found ${data.recommendations.length} career paths. The strongest match is ${data.recommendations[0].career}.`);
  } catch (error) {
    renderError(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Recommend Careers";
  }
}

async function submitChat(event) {
  event.preventDefault();

  const input = document.getElementById("chatInput");
  const button = document.getElementById("chatSubmitButton");
  const message = input.value.trim();
  if (!message) {
    return;
  }

  input.value = "";
  button.disabled = true;
  addChatBubble("user", message);
  const pendingBubble = addChatBubble("assistant", "Thinking...");
  chatHistory.push({ role: "user", content: message });

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        profile: lastProfile,
        recommendations: lastRecommendations,
        history: chatHistory,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Assistant failed");
    }

    pendingBubble.textContent = data.answer;
    chatHistory.push({ role: "assistant", content: data.answer });
  } catch (error) {
    pendingBubble.textContent = error.message || "Assistant failed. Please try again.";
  } finally {
    button.disabled = false;
    input.focus();
  }
}

function toggleAssistant() {
  const widget = document.getElementById("assistantWidget");
  const icon = document.getElementById("assistantToggleIcon");
  const collapsed = widget.classList.toggle("collapsed");
  icon.textContent = collapsed ? "+" : "-";
  document.getElementById("assistantToggle").setAttribute("aria-expanded", String(!collapsed));
}

renderCheckboxes("skillsGrid", skills, defaultSkills);
renderCheckboxes("interestsGrid", interests, defaultInterests);
document.getElementById("profileForm").addEventListener("submit", submitProfile);
document.getElementById("chatForm").addEventListener("submit", submitChat);
document.getElementById("assistantToggle").addEventListener("click", toggleAssistant);
checkApiStatus();
