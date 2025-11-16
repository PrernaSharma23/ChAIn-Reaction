// authService.ts
import { mockUsers } from "../data/mockUsers";

export function loginUser(username: string, password: string) {
  const user = mockUsers.find(
    (u) => u.username === username && u.password === password
  );

  if (user) {
    localStorage.setItem("isLoggedIn", "true");
    return true;
  }

  return false;
}

export function isLoggedIn() {
  return localStorage.getItem("isLoggedIn") === "true";
}

export function logoutUser() {
  localStorage.removeItem("isLoggedIn");
}
