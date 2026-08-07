import { useState } from "react";

const KEY = "reachrich-public-privacy";

export function usePrivacy() {
  const [hidden, setHidden] = useState(() => localStorage.getItem(KEY) === "hidden");
  const toggle = () => {
    setHidden((current) => {
      const next = !current;
      localStorage.setItem(KEY, next ? "hidden" : "visible");
      return next;
    });
  };
  return { hidden, toggle };
}
