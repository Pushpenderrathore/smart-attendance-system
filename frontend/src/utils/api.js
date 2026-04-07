const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

// Token is stored as "token" key — matches backend { "token": "..." }
function getToken() {
  return localStorage.getItem("token");
}

async function request(method, path, body = null) {
  const token = getToken();

  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, options);
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

// ── Session API ────────────────────────────────────────────
export const startSession = (payload) =>
  request("POST", "/session/start", payload);

export const refreshOTP = (sessionId) =>
  request("POST", `/session/refresh-otp/${sessionId}`);

export const endSession = (sessionId) =>
  request("POST", `/session/end/${sessionId}`);

export const getSessionStatus = (sessionId) =>
  request("GET", `/session/status/${sessionId}`);

// ── Attendance API ─────────────────────────────────────────
export const markAttendance = (payload) =>
  request("POST", "/attendance/mark", payload);

export const listAttendance = (sessionId) =>
  request("GET", `/attendance/list/${sessionId}`);

// ── Teacher API ────────────────────────────────────────────
// Backend route: GET /teacher/sessions (no teacherId in URL — comes from JWT)
export const getTeacherSessions = () =>
  request("GET", "/teacher/sessions");

export const getSessionReport = (sessionId) =>
  request("GET", `/teacher/report/${sessionId}`);

export const getFlaggedRecords = (sessionId) =>
  request("GET", `/teacher/flagged/${sessionId}`);

// ── Auth API ───────────────────────────────────────────────
export const loginUser = (userId, password) =>
  request("POST", "/auth/login", { user_id: userId, password });

export const logoutUser = () =>
  request("POST", "/auth/logout");