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
  ["sales", "Sales"],
  ["marketing", "Marketing"],
  ["digital_marketing", "Digital Marketing"],
  ["accounting", "Accounting"],
  ["financial_analysis", "Financial Analysis"],
  ["teaching", "Teaching"],
  ["content_writing", "Content Writing"],
  ["video_editing", "Video Editing"],
  ["public_speaking", "Public Speaking"],
  ["customer_service", "Customer Service"],
  ["nursing", "Nursing"],
  ["patient_care", "Patient Care"],
  ["legal_research", "Legal Research"],
  ["operations", "Operations"],
  ["project_management", "Project Management"],
  ["agriculture", "Agriculture"],
  ["culinary_skills", "Culinary Skills"],
  ["event_management", "Event Management"],
  ["photography", "Photography"],
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
const runtimeConfig = window.CAREER_ENGINE_CONFIG || {};
const apiBaseUrl = String(runtimeConfig.apiBaseUrl || "").replace(/\/$/, "");
const selectedSkills = new Map(skills.filter(([value]) => defaultSkills.has(value)));
let lastProfile = null;
let lastRecommendations = [];
let chatHistory = [];
let authMode = "login";
let authConfig = { supabase_configured: false, supabase_url: "", supabase_anon_key: "" };
let csrfToken = "";

function apiUrl(path) {
  return `${apiBaseUrl}${path}`;
}

function apiFetch(path, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  const headers = { ...(options.headers || {}) };
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(apiUrl(path), {
    ...options,
    credentials: "include",
    headers,
  });
}

async function loadAuthConfig() {
  const response = await apiFetch("/api/config");
  if (!response.ok) {
    throw new Error("Unable to load authentication configuration.");
  }
  authConfig = await response.json();
}

function supabaseConfigured() {
  return Boolean(authConfig.supabase_configured && authConfig.supabase_url && authConfig.supabase_anon_key);
}

async function supabaseAuthRequest(path, options = {}) {
  const response = await fetch(`${authConfig.supabase_url}/auth/v1${path}`, {
    ...options,
    headers: {
      apikey: authConfig.supabase_anon_key,
      Authorization: `Bearer ${authConfig.supabase_anon_key}`,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.msg || data.error_description || data.error || "Authentication failed.");
  }
  return data;
}

async function restoreSession() {
  const response = await apiFetch("/api/session/me");
  const data = await response.json().catch(() => ({}));
  if (response.ok && data.csrf_token) {
    csrfToken = data.csrf_token;
  }
  return response.ok;
}

async function createBackendSession(session) {
  const response = await apiFetch("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      access_token: session.access_token,
      refresh_token: session.refresh_token,
      expires_at: session.expires_at,
    }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Unable to create secure session.");
  }
  csrfToken = data.csrf_token || "";
}

async function handleAuthRedirect() {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const accessToken = params.get("access_token");
  if (!accessToken) {
    return false;
  }

  const session = {
    access_token: accessToken,
    refresh_token: params.get("refresh_token"),
    expires_at: Number(params.get("expires_at")) || null,
  };
  await createBackendSession(session);
  history.replaceState(null, "", window.location.pathname + window.location.search);
  showApp();
  return true;
}

function setAuthError(message) {
  const error = document.getElementById("authError");
  error.textContent = message;
  error.hidden = !message;
}

function showApp() {
  document.getElementById("startupShell").hidden = true;
  document.getElementById("authShell").hidden = true;
  document.getElementById("appShell").hidden = false;
  document.getElementById("assistantWidget").hidden = false;
  checkApiStatus();
}

function showAuth() {
  document.getElementById("startupShell").hidden = true;
  document.getElementById("authShell").hidden = false;
  document.getElementById("appShell").hidden = true;
  document.getElementById("assistantWidget").hidden = true;
}

function setAuthMode(mode) {
  authMode = mode;
  const isSignup = mode === "signup";
  document.getElementById("loginTab").classList.toggle("active", !isSignup);
  document.getElementById("signupTab").classList.toggle("active", isSignup);
  document.getElementById("loginTab").setAttribute("aria-selected", String(!isSignup));
  document.getElementById("signupTab").setAttribute("aria-selected", String(isSignup));
  document.getElementById("nameField").hidden = !isSignup;
  document.getElementById("authModeLabel").textContent = isSignup ? "Create Account" : "Welcome Back";
  document.getElementById("authTitle").textContent = isSignup ? "Create your Rajora account" : "Login to Rajora Career Engine";
  document.getElementById("authSubtitle").textContent = isSignup
    ? "Start a career recommendation session with your email."
    : "Use your email to continue your recommendation session.";
  document.getElementById("authSubmitButton").textContent = isSignup ? "Create Account" : "Login";
  document.getElementById("authPassword").autocomplete = isSignup ? "new-password" : "current-password";
  setAuthError("");
}

function validEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function isExistingSignupResponse(data) {
  return Boolean(
    data.user
    && Array.isArray(data.user.identities)
    && data.user.identities.length === 0
  );
}

function submitAuth(event) {
  event.preventDefault();
  authenticateWithEmail();
}

async function authenticateWithEmail() {
  const name = document.getElementById("authName").value.trim();
  const email = document.getElementById("authEmail").value.trim().toLowerCase();
  const password = document.getElementById("authPassword").value;
  const button = document.getElementById("authSubmitButton");

  if (authMode === "signup" && name.length < 2) {
    setAuthError("Enter your full name.");
    return;
  }
  if (!validEmail(email)) {
    setAuthError("Enter a valid email address.");
    return;
  }
  if (password.length < 8) {
    setAuthError("Password must be at least 8 characters.");
    return;
  }

  button.disabled = true;
  setAuthError("");

  try {
    if (!supabaseConfigured()) {
      throw new Error("Authentication is not configured.");
    }

    if (authMode === "signup") {
      const data = await supabaseAuthRequest("/signup", {
        method: "POST",
        body: JSON.stringify({ email, password, data: { full_name: name } }),
      });
      if (isExistingSignupResponse(data)) {
        setAuthError("Account already exists. Please login with this email instead.");
        setAuthMode("login");
        document.getElementById("authEmail").value = email;
        return;
      }
      if (!data.session && !data.access_token) {
        setAuthError("Account created. Check your email to confirm your Supabase account, then login.");
        return;
      }
      await createBackendSession(data.session || data);
    } else {
      const data = await supabaseAuthRequest("/token?grant_type=password", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      await createBackendSession(data);
    }
    showApp();
  } catch (error) {
    setAuthError(error.message || "Authentication failed.");
  } finally {
    button.disabled = false;
  }
}

function handleGoogleAuth() {
  if (!supabaseConfigured()) {
    setAuthError("Add SUPABASE_URL and SUPABASE_ANON_KEY in .env to enable Google login.");
    return;
  }
  const redirectTo = encodeURIComponent(window.location.origin + window.location.pathname);
  window.location.href = `${authConfig.supabase_url}/auth/v1/authorize?provider=google&redirect_to=${redirectTo}`;
}

async function logout() {
  await apiFetch("/api/session/logout", { method: "POST" }).catch(() => {});
  csrfToken = "";
  showAuth();
}

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

function normalizeSkill(value) {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function formatSkill(value) {
  return normalizeSkill(value)
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function findCatalogSkill(value) {
  const key = normalizeSkill(value);
  return skills.find(([skillValue, label]) => skillValue === key || normalizeSkill(label) === key);
}

function addSkill(value, label = formatSkill(value)) {
  const catalogSkill = findCatalogSkill(value);
  const key = catalogSkill ? catalogSkill[0] : normalizeSkill(value);
  if (!key) {
    return;
  }

  selectedSkills.set(key, catalogSkill ? catalogSkill[1] : label.trim() || formatSkill(key));
  renderSelectedSkills();
}

function removeSkill(value) {
  selectedSkills.delete(value);
  renderSelectedSkills();
}

function renderSelectedSkills() {
  const container = document.getElementById("skillsGrid");
  container.replaceChildren();

  selectedSkills.forEach((label, value) => {
    const chip = document.createElement("button");
    chip.className = "selected-skill";
    chip.type = "button";
    chip.textContent = `${label} x`;
    chip.addEventListener("click", () => removeSkill(value));
    container.appendChild(chip);
  });
}

function skillMatches(query) {
  const normalizedQuery = normalizeSkill(query);
  if (!normalizedQuery) {
    return [];
  }

  return skills
    .filter(([value, label]) => {
      const searchable = `${value} ${label}`.toLowerCase();
      return searchable.includes(normalizedQuery.replaceAll("_", " "));
    })
    .sort(([firstValue], [secondValue]) => {
      const firstStarts = firstValue.startsWith(normalizedQuery) ? 0 : 1;
      const secondStarts = secondValue.startsWith(normalizedQuery) ? 0 : 1;
      return firstStarts - secondStarts;
    })
    .slice(0, 8);
}

function renderSkillSuggestions(query) {
  const container = document.getElementById("skillSuggestions");
  const matches = skillMatches(query);
  const normalizedQuery = normalizeSkill(query);
  container.replaceChildren();

  matches.forEach(([value, label]) => {
    const option = document.createElement("button");
    option.type = "button";
    option.className = "skill-suggestion";
    option.textContent = label;
    option.addEventListener("click", () => {
      addSkill(value, label);
      document.getElementById("skillSearchInput").value = "";
      container.replaceChildren();
    });
    container.appendChild(option);
  });

  if (normalizedQuery && !selectedSkills.has(normalizedQuery)) {
    const customOption = document.createElement("button");
    customOption.type = "button";
    customOption.className = "skill-suggestion custom";
    customOption.textContent = `Add "${formatSkill(normalizedQuery)}"`;
    customOption.addEventListener("click", () => {
      addSkill(normalizedQuery);
      document.getElementById("skillSearchInput").value = "";
      container.replaceChildren();
    });
    container.appendChild(customOption);
  }
}

function setupSkillSearch() {
  const input = document.getElementById("skillSearchInput");

  input.addEventListener("input", () => renderSkillSuggestions(input.value));
  input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") {
      return;
    }

    event.preventDefault();
    addSkill(input.value);
    input.value = "";
    document.getElementById("skillSuggestions").replaceChildren();
  });
}

function numberValue(formData, key) {
  const value = formData.get(key);
  return value === "" || value === null ? null : Number(value);
}

function selectedValues(containerId) {
  return Array.from(document.querySelectorAll(`#${containerId} input:checked`)).map((input) => input.value);
}

function selectedSkillValues() {
  return Array.from(selectedSkills.keys());
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

function requiredSkills(recommendation) {
  return [...recommendation.matched_skills, ...recommendation.missing_skills];
}

function weeklyPlan(recommendation) {
  const missingSkills = recommendation.missing_skills.length
    ? recommendation.missing_skills
    : ["role-specific advanced practice"];
  const firstSkills = missingSkills.slice(0, 2).join(", ");
  const nextSkills = missingSkills.slice(2, 5).join(", ") || "portfolio refinement";

  return [
    {
      week: "Week 1",
      title: "Understand the role",
      actions: [
        `Study what a ${recommendation.career} does day to day.`,
        `Review all required skills: ${requiredSkills(recommendation).join(", ")}.`,
      ],
    },
    {
      week: "Week 2",
      title: "Build core gaps",
      actions: [
        `Focus on ${firstSkills}.`,
        "Complete small practice tasks and keep notes of what you learn.",
      ],
    },
    {
      week: "Week 3",
      title: "Apply through a project",
      actions: [
        `Build one practical project related to ${recommendation.career}.`,
        `Use or practice ${nextSkills}.`,
      ],
    },
    {
      week: "Week 4",
      title: "Prepare for opportunities",
      actions: [
        "Update your resume and portfolio with the project.",
        "Practice interview questions and apply for internships, jobs, or freelance work.",
      ],
    },
  ];
}

function appendSkillSection(container, title, values, emptyText) {
  const section = document.createElement("section");
  const heading = document.createElement("h4");
  const tags = document.createElement("div");

  section.className = "detail-section";
  tags.className = "tag-list";
  heading.textContent = title;
  appendTags(tags, values, emptyText);
  section.append(heading, tags);
  container.appendChild(section);
}

function openCareerDetail(recommendation) {
  const oldDialog = document.getElementById("careerDetailDialog");
  if (oldDialog) {
    oldDialog.remove();
  }

  const overlay = document.createElement("div");
  const dialog = document.createElement("section");
  const header = document.createElement("div");
  const titleGroup = document.createElement("div");
  const eyebrow = document.createElement("p");
  const title = document.createElement("h3");
  const closeButton = document.createElement("button");
  const score = document.createElement("p");
  const roadmap = document.createElement("div");
  const roadmapTitle = document.createElement("h4");

  overlay.className = "career-detail-overlay";
  overlay.id = "careerDetailDialog";
  dialog.className = "career-detail";
  header.className = "career-detail-header";
  closeButton.className = "detail-close";
  closeButton.type = "button";
  closeButton.textContent = "Close";
  eyebrow.className = "eyebrow";
  score.className = "muted";
  roadmap.className = "week-plan";

  eyebrow.textContent = "Career Roadmap";
  title.textContent = recommendation.career;
  score.textContent = `${matchScorePercent(recommendation.match_score)}% match score`;
  roadmapTitle.textContent = "Week-wise development plan";

  titleGroup.append(eyebrow, title, score);
  header.append(titleGroup, closeButton);
  dialog.appendChild(header);
  appendSkillSection(dialog, "All relevant skills", requiredSkills(recommendation), "No skills listed");
  appendSkillSection(dialog, "Already matched", recommendation.matched_skills, "No direct match yet");
  appendSkillSection(dialog, "Skills to build", recommendation.missing_skills, "No major gaps");

  roadmap.appendChild(roadmapTitle);
  weeklyPlan(recommendation).forEach((item) => {
    const step = document.createElement("div");
    const heading = document.createElement("strong");
    const list = document.createElement("ul");

    step.className = "week-step";
    heading.textContent = `${item.week}: ${item.title}`;
    item.actions.forEach((action) => {
      const listItem = document.createElement("li");
      listItem.textContent = action;
      list.appendChild(listItem);
    });

    step.append(heading, list);
    roadmap.appendChild(step);
  });

  dialog.appendChild(roadmap);
  overlay.appendChild(dialog);
  document.body.appendChild(overlay);

  closeButton.addEventListener("click", () => overlay.remove());
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) {
      overlay.remove();
    }
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
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", `Open roadmap for ${recommendation.career}`);
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
    card.addEventListener("click", () => openCareerDetail(recommendation));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openCareerDetail(recommendation);
      }
    });
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
    const response = await apiFetch("/api/health");
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
    user_type: formData.get("user_type"),
    age: numberValue(formData, "age"),
    years_experience: numberValue(formData, "years_experience"),
    current_role: formData.get("current_role"),
    location_preference: formData.get("location_preference"),
    certifications: listValue(formData, "certifications"),
    skills: selectedSkillValues(),
    interests: selectedValues("interestsGrid"),
  };

  button.disabled = true;
  button.textContent = "Running Prediction";

  try {
    const response = await apiFetch("/api/recommend", {
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
    const response = await apiFetch("/api/chat", {
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

async function initApp() {
  renderSelectedSkills();
  renderCheckboxes("interestsGrid", interests, defaultInterests);
  setupSkillSearch();
  document.getElementById("loginTab").addEventListener("click", () => setAuthMode("login"));
  document.getElementById("signupTab").addEventListener("click", () => setAuthMode("signup"));
  document.getElementById("authForm").addEventListener("submit", submitAuth);
  document.getElementById("googleAuthButton").addEventListener("click", handleGoogleAuth);
  document.getElementById("logoutButton").addEventListener("click", logout);
  document.getElementById("profileForm").addEventListener("submit", submitProfile);
  document.getElementById("chatForm").addEventListener("submit", submitChat);
  document.getElementById("assistantToggle").addEventListener("click", toggleAssistant);
  setAuthMode("login");

  try {
    await loadAuthConfig();
    if (await handleAuthRedirect()) {
      return;
    }
  } catch (error) {
    setAuthError(error.message);
    showAuth();
    return;
  }

  if (await restoreSession().catch(() => false)) {
    showApp();
  } else {
    showAuth();
  }
}

initApp();
