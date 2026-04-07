const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

// ── Token storage helpers ──────────────────────────────────

export function getToken() {
  // Check expiry before returning
  const expiry = localStorage.getItem("token_expiry");
  if (expiry && Date.now() > parseInt(expiry, 10)) {
    clearSession();
    return null;
  }
  return localStorage.getItem("token");
}

export function saveSession(token, expiresIn = 3600) {
  localStorage.setItem("token", token);
  localStorage.setItem("token_expiry", Date.now() + expiresIn * 1000);
}

export function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("token_expiry");
}

// ── Core request helper ────────────────────────────────────

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
    // If backend says token expired, clear local storage immediately
    if (res.status === 401) {
      clearSession();
      window.location.reload(); // forces back to login screen
    }
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

// ── Auth API ───────────────────────────────────────────────

export const loginUser = async (userId, password) => {
  const data = await request("POST", "/auth/login", { user_id: userId, password });
  // Save token immediately after successful login
  saveSession(data.token, data.expires_in || 3600);
  return data;
};

export const logoutUser = async () => {
  await request("POST", "/auth/logout");
  clearSession();
};

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

export const getTeacherSessions = () =>
  request("GET", "/teacher/sessions");

export const getSessionReport = (sessionId) =>
  request("GET", `/teacher/report/${sessionId}`);

export const getFlaggedRecords = (sessionId) =>
  request("GET", `/teacher/flagged/${sessionId}`);