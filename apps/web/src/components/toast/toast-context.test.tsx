import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ToastProvider, useToast } from "./toast-context";

function TriggerButton({ type, message }: { type: "success" | "error" | "info"; message: string }) {
  const { showToast } = useToast();
  return (
    <button type="button" onClick={() => showToast(type, message)}>
      Trigger
    </button>
  );
}

describe("ToastProvider / useToast", () => {
  it("throws when useToast is used outside a provider", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<TriggerButton type="info" message="x" />)).toThrow(
      "useToast must be used within a ToastProvider",
    );
    consoleError.mockRestore();
  });

  it("shows a toast with the right type styling when triggered", async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TriggerButton type="error" message="Something failed." />
      </ToastProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Trigger" }));

    const toast = await screen.findByRole("alert");
    expect(toast).toHaveTextContent("Something failed.");
  });

  it("dismisses a toast when its close button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TriggerButton type="success" message="Saved." />
      </ToastProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Trigger" }));
    await screen.findByText("Saved.");

    await user.click(screen.getByRole("button", { name: "Dismiss notification" }));

    expect(screen.queryByText("Saved.")).not.toBeInTheDocument();
  });

  it("auto-dismisses a toast after the timeout", () => {
    vi.useFakeTimers();
    render(
      <ToastProvider>
        <TriggerButton type="info" message="Heads up." />
      </ToastProvider>,
    );

    act(() => {
      fireEvent.click(screen.getByRole("button", { name: "Trigger" }));
    });
    expect(screen.getByText("Heads up.")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(screen.queryByText("Heads up.")).not.toBeInTheDocument();
    vi.useRealTimers();
  });
});
