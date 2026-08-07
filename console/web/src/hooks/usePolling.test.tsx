import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { usePolling } from "./usePolling";

let visibility: DocumentVisibilityState;
const originalVisibility = Object.getOwnPropertyDescriptor(document, "visibilityState");

function setVisibility(next: DocumentVisibilityState) {
  visibility = next;
  document.dispatchEvent(new Event("visibilitychange"));
}

beforeEach(() => {
  vi.useFakeTimers();
  visibility = "visible";
  Object.defineProperty(document, "visibilityState", {
    configurable: true,
    get: () => visibility,
  });
});

afterEach(() => {
  vi.useRealTimers();
  if (originalVisibility) Object.defineProperty(document, "visibilityState", originalVisibility);
});

describe("usePolling", () => {
  it("pauses interval work while hidden and refreshes immediately on return", async () => {
    const load = vi.fn().mockResolvedValue({ status: "ok" });
    const { unmount } = renderHook(() => usePolling(load, 1_000));
    await act(async () => undefined);
    expect(load).toHaveBeenCalledTimes(1);

    act(() => setVisibility("hidden"));
    await act(async () => vi.advanceTimersByTime(3_000));
    expect(load).toHaveBeenCalledTimes(1);

    await act(async () => setVisibility("visible"));
    expect(load).toHaveBeenCalledTimes(2);

    await act(async () => vi.advanceTimersByTime(1_000));
    expect(load).toHaveBeenCalledTimes(3);
    unmount();
  });
});
