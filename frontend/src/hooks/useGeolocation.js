import { useState, useCallback } from "react";

export function useGeolocation() {
  const [coords, setCoords] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const getLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser.");
      return Promise.reject("Unsupported");
    }

    setLoading(true);
    setError(null);

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const loc = {
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
          };
          setCoords(loc);
          setLoading(false);
          resolve(loc);
        },
        (err) => {
          const messages = {
            1: "Location permission denied. Please allow access.",
            2: "Location unavailable. Check your GPS.",
            3: "Location request timed out. Please try again.",
          };
          const msg = messages[err.code] || "Unknown location error.";
          setError(msg);
          setLoading(false);
          reject(msg);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    });
  }, []);

  return { coords, error, loading, getLocation };
}
