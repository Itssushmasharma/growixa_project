import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Without `test.globals: true`, RTL's own auto-cleanup side effect (which looks for a
// global `afterEach`) never registers — without this, DOM from one test in a file leaks
// into the next.
afterEach(() => {
  cleanup();
});
