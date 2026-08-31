"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Button from "../primitives/button";
import Tag from "../primitives/tag";
import { hueVars } from "../layout/section";
import { STAGES, STATUS, type Stage } from "@/content/website/stages";
import { SOLUTIONS } from "@/content/website/nav";
import styles from "./mobile-nav.module.css";

const DIRECT = [
  { to: "/pricing", label: "Pricing" },
  { to: "/roadmap", label: "Roadmap" },
  { to: "/sandbox", label: "Sandbox" },
  { to: "/stack-calculator", label: "Stack calculator" },
  { to: "/docs", label: "Documentation" },
];

function label(stage: Stage) {
  return stage.status === STATUS.SOON ? `Coming ${stage.statusLabel}` : stage.statusLabel;
}

export default function MobileNav() {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close on navigation. Without this the drawer stays over the new page.
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) return undefined;

    // Lock the page behind the drawer, and restore whatever overflow was there.
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
        return;
      }
      if (e.key !== "Tab" || !panelRef.current) return;

      // Keep Tab inside the drawer: everything behind it is inert.
      const items = panelRef.current.querySelectorAll<HTMLElement>(
        "a[href], button:not([disabled])",
      );
      const first = items[0];
      const last = items[items.length - 1];
      if (first && last) {
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", onKey);
    panelRef.current?.querySelector<HTMLElement>("a[href], button")?.focus();

    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open]);

  return (
    <div className={styles.root}>
      <button
        type="button"
        ref={triggerRef}
        className={styles.trigger}
        aria-expanded={open}
        aria-controls="mobile-nav"
        aria-label={open ? "Close menu" : "Open menu"}
        onClick={() => setOpen((v) => !v)}
      >
        <span className={`${styles.bars} ${open ? styles.barsOpen : ""}`} aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
      </button>

      {open &&
        mounted &&
        createPortal(
          <>
            <div className={styles.scrim} onClick={() => setOpen(false)} aria-hidden="true" />
            <nav id="mobile-nav" className={styles.panel} ref={panelRef} aria-label="Mobile">
              <p className={styles.group}>The Engine</p>
              {STAGES.map((s) => (
                <Link key={s.id} href={s.path} className={styles.stage} style={hueVars(s.hue)}>
                  <i className={styles.dot} aria-hidden="true" />
                  <span className={styles.stageText}>
                    <b>{s.name}</b>
                    <span>{s.blurb}</span>
                  </span>
                  <Tag status={s.status} label={label(s)} />
                </Link>
              ))}
              <Link href="/platform" className={styles.item}>
                How it fits together
              </Link>

              <p className={styles.group}>Solutions</p>
              {SOLUTIONS.map((s) => (
                <Link key={s.id} href={s.path} className={styles.item}>
                  For {s.name.toLowerCase()}
                </Link>
              ))}

              <p className={styles.group}>Product</p>
              {DIRECT.map((d) => (
                <Link key={d.to} href={d.to} className={styles.item}>
                  {d.label}
                </Link>
              ))}

              <div className={styles.actions}>
                <Button as={Link} href="/register" className={styles.full}>
                  Start free
                </Button>
                <Button as={Link} href="/login" variant="glass" className={styles.full}>
                  Log in
                </Button>
              </div>

              <p className={styles.honest}>
                Campaigns and contacts are live. Find and Create are in beta. Qualify ships Q4.
              </p>
            </nav>
          </>,
          document.body,
        )}
    </div>
  );
}
