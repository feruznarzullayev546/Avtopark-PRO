import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    try { return localStorage.getItem("avtopark-theme") === "dark" ? "dark" : "light"; } catch { return "light"; }
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("avtopark-theme", theme); } catch { /* storage can be disabled */ }
  }, [theme]);
  return <button type="button" className="ap-theme-toggle" aria-label={theme === "light" ? "To‘q rejimga o‘tish" : "Yorug‘ rejimga o‘tish"} onClick={() => setTheme(t => t === "light" ? "dark" : "light")}>
    {theme === "light" ? <Moon size={17}/> : <Sun size={17}/>}<span>{theme === "light" ? "Dark" : "Light"}</span>
  </button>;
}
