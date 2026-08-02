import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Without `test.globals: true`, RTL's own auto-cleanup side effect (which looks for a
// global `afterEach`) never registers — without this, DOM from one test in a file leaks
// into the next.
afterEach(() => {
  cleanup();
});

// jsdom doesn't implement matchMedia at all — anything using a responsive breakpoint
// check (e.g. the dashboard shell's mobile sidebar default) throws without this.
// Defaults to "not matching" (desktop); individual tests override via
// vi.spyOn(window, "matchMedia") when they need to simulate a mobile viewport.
if (!window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}
