const API_BASE = "http://localhost:8000";

export async function fetchTargets(params = {}) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== "") {
      searchParams.set(key, String(value));
    }
  });

  const response = await fetch(`${API_BASE}/targets?${searchParams.toString()}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
