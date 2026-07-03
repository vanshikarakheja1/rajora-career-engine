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
const maxChatHistory = 20;
let lastProfile = null;
let lastRecommendations = [];
let chatHistory = [];

function renderCheckboxes(containerId, values, selectedValues) {
  const container = document.getElementById(containerId);
  container.replaceChildren();

  values.forEach(([value, label]) => {
    const chip = document.createElement("label");
    const input = document.createElement("input");
    const text = document.createElement("span");

    chip.className = "chip";
    input.type = "checkbox";
    input.value = value;
    input.checked = selectedValues.has(value);
    text.textContent = label;

    chip.append(input, text);
    container.appendChild(chip);
  });
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

function matchScorePercent(value) {
  return Math.round(Number(value) * 100);
}

function appendTags(container, values, emptyText) {
  container.replaceChildren();

  if (!values.length) {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = emptyText;
    container.appendChild(tag);
    return;
  }

  values.forEach((value) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = value;
    container.appendChild(tag);
  });
}

function appendRoadmap(container, steps) {
  steps.forEach((step) => {
    const stepElement = document.createElement("div");
    const title = document.createElement("strong");
    const actions = document.createElement("ul");

    stepElement.className = "roadmap-step";
    title.textContent = step.title;

    step.actions.forEach((action) => {
      const item = document.createElement("li");
      item.textContent = action;
      actions.appendChild(item);
    });

    stepElement.append(title, actions);
    container.appendChild(stepElement);
  });
}

function renderRecommendations(recommendations) {
  const results = document.getElementById("results");
  const emptyState = document.getElementById("emptyState");

  emptyState.style.display = "none";
  results.replaceChildren();

  recommendations.forEach((recommendation) => {
    const percent = matchScorePercent(recommendation.match_score);
    const card = document.createElement("article");
    const topLine = document.createElement("div");
    const titleGroup = document.createElement("div");
    const title = document.createElement("h3");
    const subtitle = document.createElement("p");
    const score = document.createElement("div");
    const meter = document.createElement("div");
    const meterFill = document.createElement("span");
    const skillRow = document.createElement("div");
    const matchedBox = document.createElement("div");
    const missingBox = document.createElement("div");
    const matchedTitle = document.createElement("h4");
    const missingTitle = document.createElement("h4");
    const matchedTags = document.createElement("div");
    const missingTags = document.createElement("div");
    const roadmap = document.createElement("div");
    const roadmapTitle = document.createElement("h4");

    card.className = "career-card";
    topLine.className = "career-topline";
    title.className = "career-title";
    subtitle.className = "muted";
    score.className = "match-score";
    meter.className = "meter";
    skillRow.className = "skill-row";
    matchedBox.className = "skill-box";
    missingBox.className = "skill-box";
    matchedTags.className = "tag-list";
    missingTags.className = "tag-list";
    roadmap.className = "roadmap";

    title.textContent = recommendation.career;
    subtitle.textContent = "Career match based on your current profile";
    score.textContent = `${percent}%`;
    score.setAttribute("aria-label", `${percent}% match score`);
    meterFill.style.width = `${percent}%`;
    matchedTitle.textContent = "Matched Skills";
    missingTitle.textContent = "Skills To Build";
    roadmapTitle.textContent = "Roadmap";

    appendTags(matchedTags, recommendation.matched_skills, "No direct match yet");
    appendTags(missingTags, recommendation.missing_skills, "No major gap");
    appendRoadmap(roadmap, recommendation.roadmap);

    titleGroup.append(title, subtitle);
    topLine.append(titleGroup, score);
    meter.appendChild(meterFill);
    matchedBox.append(matchedTitle, matchedTags);
    missingBox.append(missingTitle, missingTags);
    skillRow.append(matchedBox, missingBox);
    roadmap.prepend(roadmapTitle);
    card.append(topLine, meter, skillRow, roadmap);
    results.appendChild(card);
  });
}

function renderError(message) {
  const error = document.createElement("div");
  error.className = "error-message";
  error.textContent = message;

  document.getElementById("emptyState").style.display = "none";
  document.getElementById("results").replaceChildren(error);
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

function addChatHistory(role, content) {
  chatHistory.push({ role, content });
  chatHistory = chatHistory.slice(-maxChatHistory);
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
  addChatHistory("user", message);

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
    addChatHistory("assistant", data.answer);
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
