// src/services/authService.ts

export async function loginUser(username: string, password: string) {
  try {
    const res = await fetch("https://misty-mousy-unseparately.ngrok-free.dev/api/user/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) return { success: false, error: "Invalid credentials" };

    const data = await res.json();

    // Extract & normalize repos
    const repoMap: Record<string, string> = {};
    (data.profile?.repos || []).forEach((r: any) => {
      repoMap[String(r.id)] = r.name;  // ID → string
    });

    // Save minimal info in sessionStorage
    sessionStorage.setItem("isLoggedIn", "true");
    sessionStorage.setItem("token", data.token);
    sessionStorage.setItem("repoMap", JSON.stringify(repoMap));

    return { success: true };

  } catch (err) {
    return { success: false, error: "Network error" };
  }
}

export function isLoggedIn() {
  return sessionStorage.getItem("isLoggedIn") === "true";
}

export function logoutUser() {
  sessionStorage.clear();
}
