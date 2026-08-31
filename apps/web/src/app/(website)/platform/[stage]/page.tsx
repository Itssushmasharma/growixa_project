import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { STAGES, getStage } from "@/content/website/stages";
import { STAGE_PAGES } from "@/content/website/stage-pages";
import {
  PageHero,
  Sec,
  Head,
  Steps,
  Bento,
  Surface,
  PrevNext,
  ClosingCta,
  Tag,
  Button,
  statusLabel,
} from "@/components/website/sections/page-kit";

interface StagePageProps {
  params: Promise<{ stage: string }>;
}

export async function generateStaticParams() {
  return STAGES.map((s) => ({ stage: s.id }));
}

export async function generateMetadata({ params }: StagePageProps): Promise<Metadata> {
  const { stage: stageId } = await params;
  const stage = getStage(stageId);
  const page = STAGE_PAGES[stageId];

  if (!stage || !page) {
    return { title: "Stage Not Found — Growixa" };
  }

  return {
    title: `${stage.num} — ${stage.name} | Growixa Engine`,
    description: page.lede,
  };
}

export default async function StageDetailPage({ params }: StagePageProps) {
  const { stage: stageId } = await params;
  const stage = getStage(stageId);
  const page = STAGE_PAGES[stageId];
  const i = STAGES.findIndex((s) => s.id === stageId);

  if (!stage || !page) {
    notFound();
  }

  return (
    <>
      <PageHero
        hue={stage.hue}
        eyebrow={`${stage.num} — ${stage.name.toUpperCase()}`}
        tag={<Tag status={stage.status} label={statusLabel(stage)} />}
        title={page.title}
        lede={page.lede}
        foot={page.foot}
        actions={
          <>
            <Button as={Link} href={page.cta.to === "/pricing" ? "/register" : page.cta.to}>
              {page.cta.label}
            </Button>
            <Button as={Link} href="/platform" variant="glass">
              See the whole engine
            </Button>
          </>
        }
        aside={<Surface {...page.surface} />}
      />

      <Sec hue={stage.hue}>
        <Head {...page.stepsHead} />
        <Steps items={page.steps} />
      </Sec>

      <Sec tint hue={stage.hue}>
        <Head {...page.featHead} />
        <Bento items={page.features} />
      </Sec>

      <Sec hue={stage.hue}>
        <PrevNext prev={STAGES[i - 1]} next={STAGES[i + 1]} />
      </Sec>

      <ClosingCta
        title="Start where it already works."
        body="Campaigns and contacts are live and free to try. The rest of the engine switches on as it ships — no new contract, no migration."
        primary={{ to: "/register", label: "Start free" }}
        secondary={{ to: "/roadmap", label: "See the roadmap" }}
        foot="No credit card · Import your list in one click"
      />
    </>
  );
}
