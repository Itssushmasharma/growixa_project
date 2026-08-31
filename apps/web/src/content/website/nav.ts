export interface SolutionItem {
  id: string;
  name: string;
  blurb: string;
  hue: string;
  path: string;
}

export const SOLUTIONS: SolutionItem[] = [
  {
    id: "founders",
    name: "Founders",
    blurb: "You are the GTM team. For now.",
    hue: "send",
    path: "/for/founders",
  },
  {
    id: "gtm-teams",
    name: "GTM teams",
    blurb: "Replace the stack you inherited.",
    hue: "find",
    path: "/for/gtm-teams",
  },
  {
    id: "marketing-teams",
    name: "Marketing teams",
    blurb: "Campaigns without the tool tax.",
    hue: "create",
    path: "/for/marketing-teams",
  },
];
