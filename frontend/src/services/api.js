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

export async function fetchNotifications() {
  try {
    const response = await fetch(`${BASE_URL}/notifications`);
    if (!response.ok) throw new Error("Failed to fetch notifications");
    return await response.json();
  } catch (error) {
    console.error("API Error (Notifications):", error);
    return { notifications: [] };
  }
}

export async function respondToEvent(eventType, responseValue) {
  try {
    const response = await fetch(`${BASE_URL}/respond?event_type=${encodeURIComponent(eventType)}&response=${responseValue}`, {
      method: "POST"
    });
    if (!response.ok) throw new Error("Failed to respond");
    return await response.json();
  } catch (error) {
    console.error("API Error (Respond):", error);
    return null;
  }
}

export async function tickTime(minutes = 30) {
  try {
    const response = await fetch(`${BASE_URL}/tick?minutes=${minutes}`, {
      method: "POST"
    });
    if (!response.ok) throw new Error("Failed to tick");
    return await response.json();
  } catch (error) {
    console.error("API Error (Tick):", error);
    return null;
  }
}
