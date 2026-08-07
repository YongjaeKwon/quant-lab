// @vitest-environment node
import { readFileSync } from "node:fs";
import { describe, expect, it, vi } from "vitest";

type Handler = (event: {
  request: { url: string; method: string };
  respondWith: ReturnType<typeof vi.fn>;
}) => void;

describe("service worker caching boundary", () => {
  it("leaves every /api request to the network without touching a cache", () => {
    const source = readFileSync(new URL("../public/sw.js", import.meta.url), "utf8");
    const handlers = new Map<string, Handler>();
    const selfMock = {
      addEventListener: vi.fn((type: string, handler: Handler) => handlers.set(type, handler)),
    };
    const cachesMock = { open: vi.fn(), match: vi.fn() };
    const fetchMock = vi.fn();
    new Function("self", "caches", "fetch", source)(selfMock, cachesMock, fetchMock);

    const respondWith = vi.fn();
    handlers.get("fetch")?.({
      request: { url: "https://portfolio.example/api/account/summary", method: "GET" },
      respondWith,
    });

    expect(respondWith).not.toHaveBeenCalled();
    expect(fetchMock).not.toHaveBeenCalled();
    expect(cachesMock.open).not.toHaveBeenCalled();
    expect(cachesMock.match).not.toHaveBeenCalled();
  });
});
