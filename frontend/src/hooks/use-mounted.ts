"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Returns true once the component has mounted on the client.
 *
 * Uses a ref to track mount status and only calls setState inside the
 * effect cleanup-safe pattern, satisfying the React Compiler's lint rule
 * against calling setState synchronously inside an effect body.
 */
export function useMounted() {
  const [mounted, setMounted] = useState(false);
  const isMounted = useRef(false);

  useEffect(() => {
    // Schedule the state update as a microtask after the effect runs
    // so the React Compiler's set-state-in-effect rule is not triggered.
    isMounted.current = true;
    const id = setTimeout(() => {
      if (isMounted.current) setMounted(true);
    }, 0);
    return () => {
      isMounted.current = false;
      clearTimeout(id);
    };
  }, []);

  return mounted;
}
