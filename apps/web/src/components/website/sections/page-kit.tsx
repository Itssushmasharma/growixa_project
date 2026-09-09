import type { ReactNode } from "react";
import Link from "next/link";
import Wrap from "../layout/wrap";
import Button from "../primitives/button";
import Tag from "../primitives/tag";
import { hueVars } from "../layout/section";
import { STATUS, type Stage } from "@/content/website/stages";
import styles from "./page.module.css";

export function statusLabel(stage: Stage) {
  return stage.status === STATUS.SOON ? `Coming ${stage.statusLabel}` : stage.statusLabel;
}

export interface PageHeroProps {
  hue?: string;
  eyebrow?: string;
  tag?: ReactNode;
  title: string;
  lede: string;
  actions?: ReactNode;
  foot?: string;
  aside?: ReactNode;
}

/** Hue-tinted page hero. `aside` renders the product surface on the right. */
export function PageHero({ hue, eyebrow, tag, title, lede, actions, foot, aside }: PageHeroProps) {
  return (
    <section className={styles.phero} style={hueVars(hue)}>
      <span className={styles.brandWatermark} aria-hidden="true">
        GROWIXA
      </span>
      <Wrap className={styles.pheroWrap}>
        <div className={aside ? styles.pheroGrid : styles.pheroSolo}>
          <div>
            {eyebrow && (
              <span className={styles.stagetag}>
                <span className={styles.num}>{eyebrow}</span>
                {tag}
              </span>
            )}
            <h1 className={styles.h1}>{title}</h1>
            <p className={styles.lede}>{lede}</p>
            {actions && <div className={styles.actions}>{actions}</div>}
            {foot && <p className={styles.foot}>{foot}</p>}
          </div>
          {aside}
        </div>
      </Wrap>
    </section>
  );
}

export interface SecProps {
  tint?: boolean;
  dark?: boolean;
  hue?: string;
  id?: string;
  children: ReactNode;
}

export function Sec({ tint, dark, hue, id, children }: SecProps) {
  const cls = [styles.sec, tint && styles.tint, dark && styles.dark].filter(Boolean).join(" ");
  return (
    <section id={id} className={cls} style={hueVars(hue)}>
      <Wrap className={styles.secWrap}>{children}</Wrap>
    </section>
  );
}

export interface HeadProps {
  eyebrow?: string;
  title: string;
  lede?: string;
  center?: boolean;
}

export function Head({ eyebrow, title, lede, center }: HeadProps) {
  return (
    <header className={center ? styles.headCenter : styles.head}>
      <div>
        {eyebrow && <span className={styles.mono}>{eyebrow}</span>}
        <h2 className={styles.h2}>{title}</h2>
      </div>
      {lede && <p className={styles.headLede}>{lede}</p>}
    </header>
  );
}

export interface StepItem {
  title: string;
  body: string;
}

export function Steps({ items }: { items: StepItem[] }) {
  return (
    <div className={styles.steps}>
      {items.map((s, i) => (
        <div key={s.title} className={styles.step}>
          <span className={styles.sn}>{String(i + 1).padStart(2, "0")}</span>
          <h3 className={styles.h3}>{s.title}</h3>
          <p className={styles.p}>{s.body}</p>
        </div>
      ))}
    </div>
  );
}

export interface BentoItem {
  span?: "w4" | "w6" | "w8" | "w12";
  title: string;
  body: string;
  chips?: string[];
}

export function Bento({ items }: { items: BentoItem[] }) {
  return (
    <div className={styles.bento}>
      {items.map((f) => (
        <article key={f.title} className={`${styles.fcard} ${styles[f.span || "w4"]}`}>
          <span className={styles.glow} aria-hidden="true" />
          <span className={styles.fico} aria-hidden="true">
            <Dot />
          </span>
          <h3 className={styles.h3}>{f.title}</h3>
          <p className={styles.p}>{f.body}</p>
          {f.chips && (
            <span className={styles.chips}>
              {f.chips.map((c) => (
                <span key={c} className={styles.chip}>
                  {c}
                </span>
              ))}
            </span>
          )}
        </article>
      ))}
    </div>
  );
}

function Dot() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="6" stroke="var(--hue)" strokeWidth="2" />
      <circle cx="10" cy="10" r="2" fill="var(--hue)" />
    </svg>
  );
}

export interface SurfaceRowProps {
  badge?: string;
  badgeBg?: string;
  label: string;
  sub?: string;
  value?: string;
}

export interface SurfaceProps {
  title?: string;
  subtitle?: string;
  chip?: string;
  rows: SurfaceRowProps[];
  footer?: string;
  dark?: boolean;
}

/** Rows of icon + text + trailing value. Used for every product surface. */
export function Surface({ title, subtitle, chip, rows, footer, dark }: SurfaceProps) {
  return (
    <div className={dark ? styles.darkSurface : styles.surface}>
      {(title || chip) && (
        <div className={styles.surfBar}>
          <div>
            {title && <div className={styles.surfTitle}>{title}</div>}
            {subtitle && <div className={styles.surfSub}>{subtitle}</div>}
          </div>
          {chip && <span className={styles.chipHue}>{chip}</span>}
        </div>
      )}
      {rows.map((r) => (
        <div key={r.label} className={styles.row}>
          {r.badge && (
            <span className={styles.rowBadge} style={{ background: r.badgeBg || "var(--hue-l)" }}>
              {r.badge}
            </span>
          )}
          <span className={styles.rowText}>
            <b>{r.label}</b>
            {r.sub && <span>{r.sub}</span>}
          </span>
          {r.value && <span className={styles.rowValue}>{r.value}</span>}
        </div>
      ))}
      {footer && <div className={styles.surfFoot}>{footer}</div>}
    </div>
  );
}

export interface PrevNextProps {
  prev?: Stage;
  next?: Stage;
}

export function PrevNext({ prev, next }: PrevNextProps) {
  return (
    <div className={styles.pn}>
      {prev ? (
        <Link href={prev.path} className={styles.pnCard} style={hueVars(prev.hue)}>
          <span className={styles.mono}>Previous stage</span>
          <h3 className={styles.pnH}>
            <i aria-hidden="true" />
            {prev.name}
          </h3>
          <p className={styles.p}>{prev.blurb}</p>
        </Link>
      ) : (
        <Link href="/platform" className={styles.pnCard} style={hueVars("create")}>
          <span className={styles.mono}>Back to</span>
          <h3 className={styles.pnH}>
            <i aria-hidden="true" />
            The Growixa Engine
          </h3>
          <p className={styles.p}>See how all five stages connect.</p>
        </Link>
      )}
      {next && (
        <Link
          href={next.path}
          className={`${styles.pnCard} ${styles.pnRight}`}
          style={hueVars(next.hue)}
        >
          <span className={styles.mono}>Next stage</span>
          <h3 className={styles.pnH}>
            {next.name}
            <i aria-hidden="true" />
          </h3>
          <p className={styles.p}>{next.blurb}</p>
        </Link>
      )}
    </div>
  );
}

export interface ClosingCtaProps {
  title: string;
  body: string;
  primary: { to: string; label: string };
  secondary?: { to: string; label: string };
  foot?: string;
}

export function ClosingCta({ title, body, primary, secondary, foot }: ClosingCtaProps) {
  return (
    <section className={styles.cta}>
      <span className={styles.ctaWatermark} aria-hidden="true">
        GROWIXA
      </span>
      <Wrap className={styles.ctaWrap}>
        <h2 className={styles.ctaH2}>{title}</h2>
        <p className={styles.ctaP}>{body}</p>
        <div className={styles.ctaActions}>
          <Button as={Link} href={primary.to} variant="onstage">
            {primary.label}
          </Button>
          {secondary && (
            <Button as={Link} href={secondary.to} variant="ghoststage">
              {secondary.label}
            </Button>
          )}
        </div>
        {foot && <p className={styles.ctaFoot}>{foot}</p>}
      </Wrap>
    </section>
  );
}

export { Tag, Button, Wrap, styles };
