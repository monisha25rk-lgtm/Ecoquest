import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authService } from "../services/authService.js";
import { clearToken, getToken, setToken } from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  useEffect(() => {
    const handleUnauthorized = () => setUser(null);
    window.addEventListener("ecoquest:unauthorized", handleUnauthorized);
    const token = getToken();
    if (!token) {
      setLoading(false);
    } else {
      authService.me()
        .then(setUser)
        .catch(() => clearToken())
        .finally(() => setLoading(false));
    }
    return () => window.removeEventListener("ecoquest:unauthorized", handleUnauthorized);
  }, []);

  const login = useCallback(async (email, password, remember = true) => {
    const response = await authService.login(email, password);
    setToken(response.access_token, remember);
    setUser(response.user);
    return response.user;
  }, []);

  const register = useCallback(async (values) => authService.register(values), []);
  const value = useMemo(() => ({ user, loading, login, logout, register, setUser }), [user, loading, login, logout, register]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider.");
  return context;
}
