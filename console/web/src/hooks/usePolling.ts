import { useEffect, useState } from "react";

export function usePolling<T>(load: () => Promise<T>, intervalMs = 30_000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const tick = async () => {
      try {
        const next = await load();
        if (!active) return;
        setData(next);
        setError(null);
      } catch (caught) {
        if (active) setError(caught instanceof Error ? caught : new Error("unknown error"));
      } finally {
        if (active) setLoading(false);
      }
    };
    const tickWhenVisible = () => {
      if (document.visibilityState === "visible") void tick();
    };

    void tick();
    const timer = window.setInterval(tickWhenVisible, intervalMs);
    document.addEventListener("visibilitychange", tickWhenVisible);
    return () => {
      active = false;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", tickWhenVisible);
    };
  }, [load, intervalMs]);

  return { data, error, loading };
}
