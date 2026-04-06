const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

async function request(method, path, body = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" },
  };
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
export const getTeacherSessions = (teacherId) =>
  request("GET", `/teacher/sessions/${teacherId}`);

export const getSessionReport = (sessionId) =>
  request("GET", `/teacher/report/${sessionId}`);

export const getFlaggedRecords = (sessionId) =>
  request("GET", `/teacher/flagged/${sessionId}`);
