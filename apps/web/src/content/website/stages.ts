export const STATUS = {
  LIVE: "live",
  BETA: "beta",
  SOON: "soon",
} as const;

export type StageStatus = (typeof STATUS)[keyof typeof STATUS];

export interface Stage {
  id: "find" | "qualify" | "create" | "send" | "manage";
  num: string;
  name: string;
  hue: "find" | "qualify" | "create" | "send" | "manage";
  path: string;
  status: StageStatus;
  statusLabel: string;
  blurb: string;
  handoff: string;
}

export const STAGES: Stage[] = [
  {
    id: "find",
    num: "01",
    name: "Find",
    hue: "find",
    path: "/platform/find",
    status: STATUS.BETA,
    statusLabel: "Beta",
    blurb: "Build a verified list from a market description.",
    handoff: "Verified people + company facts",
  },
  {
    id: "qualify",
    num: "02",
    name: "Qualify",
    hue: "qualify",
    path: "/platform/qualify",
    status: STATUS.SOON,
    statusLabel: "Q4 2026",
    blurb: "Score who's in-market from real behaviour.",
    handoff: "A score and the reason for it",
  },
  {
    id: "create",
    num: "03",
    name: "Create",
    hue: "create",
    path: "/platform/create",
    status: STATUS.BETA,
    statusLabel: "Beta",
    blurb: "Writes for the channel, in your voice.",
    handoff: "Channel-ready drafts",
  },
  {
    id: "send",
    num: "04",
    name: "Send",
    hue: "send",
    path: "/platform/send",
    status: STATUS.LIVE,
    statusLabel: "Live",
    blurb: "Campaigns and sequences that reach the inbox.",
    handoff: "Opens, clicks, replies",
  },
  {
    id: "manage",
    num: "05",
    name: "Manage",
    hue: "manage",
    path: "/platform/manage",
    status: STATUS.LIVE,
    statusLabel: "Live",
    blurb: "One record per person. Everything writes to it.",
    handoff: "Everything, back to stage one",
  },
];

export function getStage(id: string): Stage | undefined {
  return STAGES.find((s) => s.id === id);
}
