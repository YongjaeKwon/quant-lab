import { useEffect, useState } from "react";

export type ThemeMode = "light" | "dark" | "system";
const KEY = "reachrich-public-theme";
const ORDER: ThemeMode[] = ["light", "dark", "system"];

function storedTheme(): ThemeMode {
  const value = localStorage.getItem(KEY);
  return value === "light" || value === "dark" || value === "system" ? value : "system";
}

export function useTheme() {
  const [mode, setMode] = useState<ThemeMode>(storedTheme);

  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
      const resolved = mode === "system" ? (query.matches ? "dark" : "light") : mode;
      document.documentElement.dataset.theme = resolved;
    };
    apply();
    query.addEventListener("change", apply);
    return () => query.removeEventListener("change", apply);
  }, [mode]);

  const cycle = () => {
    setMode((current) => {
      const next = ORDER[(ORDER.indexOf(current) + 1) % ORDER.length];
      localStorage.setItem(KEY, next);
      return next;
    });
  };
  return { mode, cycle };
}
