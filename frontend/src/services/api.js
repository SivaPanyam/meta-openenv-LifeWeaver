const BASE_URL = "http://localhost:8000";

export async function fetchReset() {
  try {
    const response = await fetch(`${BASE_URL}/reset`);
    if (!response.ok) throw new Error("Failed to reset");
    return await response.json();
  } catch (error) {
    console.error("API Error (Reset):", error);
    return { events: [], full_state: {} };
  }
}

export async function optimize() {
  try {
    const response = await fetch(`${BASE_URL}/optimize`, {
      method: "POST"
    });
    if (!response.ok) throw new Error("Failed to optimize");
    return await response.json();
  } catch (error) {
    console.error("API Error (Optimize):", error);
    return null;
  }
}
