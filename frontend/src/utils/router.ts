import { useEffect, useState } from "react";


// Hash routes ("#/research/TCS") work on any static host without
// server-side rewrites.
function currentPath(): string[] {
  return window.location.hash
    .replace(/^#\/?/, "")
    .split("/")
    .filter(Boolean)
    .map(decodeURIComponent);
}


export function useRoute(): string[] {
  const [path, setPath] = useState(currentPath);

  useEffect(() => {
    const onChange = () => {
      setPath(currentPath());
      window.scrollTo(0, 0);
    };

    window.addEventListener("hashchange", onChange);

    return () =>
      window.removeEventListener("hashchange", onChange);
  }, []);

  return path;
}


export function navigate(...segments: string[]) {
  window.location.hash = `/${segments
    .map(encodeURIComponent)
    .join("/")}`;
}


export function researchLink(ticker: string): string {
  return `#/research/${encodeURIComponent(ticker)}`;
}
