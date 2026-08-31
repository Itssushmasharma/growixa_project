import { describe, it, expect } from "vitest";
import { STAGES, getStage, STATUS } from "./stages";

describe("STAGES", () => {
  it("has exactly five stages in engine order", () => {
    expect(STAGES.map((s) => s.id)).toEqual(["find", "qualify", "create", "send", "manage"]);
  });

  it("numbers stages 01 through 05", () => {
    expect(STAGES.map((s) => s.num)).toEqual(["01", "02", "03", "04", "05"]);
  });

  it("assigns each stage its fixed hue", () => {
    const hues = Object.fromEntries(STAGES.map((s) => [s.id, s.hue]));
    expect(hues).toEqual({
      find: "find",
      qualify: "qualify",
      create: "create",
      send: "send",
      manage: "manage",
    });
  });

  it("records the true build status for each stage", () => {
    expect(getStage("send")?.status).toBe(STATUS.LIVE);
    expect(getStage("manage")?.status).toBe(STATUS.LIVE);
    expect(getStage("find")?.status).toBe(STATUS.BETA);
    expect(getStage("create")?.status).toBe(STATUS.BETA);
    expect(getStage("qualify")?.status).toBe(STATUS.SOON);
  });

  it("gives every stage a route under /platform", () => {
    STAGES.forEach((s) => expect(s.path).toBe(`/platform/${s.id}`));
  });

  it("gives every stage a handoff description", () => {
    STAGES.forEach((s) => expect(s.handoff.length).toBeGreaterThan(0));
  });

  it("returns undefined for an unknown stage", () => {
    expect(getStage("nope")).toBeUndefined();
  });
});
