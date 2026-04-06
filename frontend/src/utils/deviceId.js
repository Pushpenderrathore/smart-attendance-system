/**
 * Generate a consistent device fingerprint from browser properties.
 * Not cryptographically secure, but sufficient for basic duplicate detection.
 */
export function getDeviceId() {
  const stored = localStorage.getItem("sas_device_id");
  if (stored) return stored;

  const raw = [
    navigator.userAgent,
    navigator.language,
    screen.width,
    screen.height,
    screen.colorDepth,
    new Date().getTimezoneOffset(),
    navigator.hardwareConcurrency || 0,
    navigator.deviceMemory || 0,
  ].join("|");

  const id = "dev_" + simpleHash(raw);
  localStorage.setItem("sas_device_id", id);
  return id;
}

function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // 32-bit
  }
  return Math.abs(hash).toString(36);
}
