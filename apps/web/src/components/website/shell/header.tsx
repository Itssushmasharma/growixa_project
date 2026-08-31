import Link from "next/link";
import MegaMenu from "./mega-menu";
import MobileNav from "./mobile-nav";
import Button from "../primitives/button";
import Wrap from "../layout/wrap";
import { STAGES } from "@/content/website/stages";
import { SOLUTIONS } from "@/content/website/nav";
import styles from "./header.module.css";

export default function Header() {
  return (
    <header className={styles.hdr}>
      <Wrap>
        <nav className={styles.nav} aria-label="Main">
          <Link href="/" className={styles.brand}>
            <span className={styles.mark} aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 14 14">
                <path d="M7.6 1 2.6 8h3.1l-.5 5 5-7H7.1z" fill="var(--ink)" />
              </svg>
            </span>
            Growixa
          </Link>

          <div className={styles.links}>
            <MegaMenu
              label="Platform"
              items={STAGES}
              footer={
                <>
                  <span className={styles.note}>
                    Email campaigns are live today — the rest ships through 2026
                  </span>
                  <Button as={Link} href="/roadmap" size="sm">
                    See the roadmap
                  </Button>
                </>
              }
            />
            <MegaMenu label="Solutions" items={SOLUTIONS} />
            <Link href="/pricing" className={styles.link}>
              Pricing
            </Link>
            <Link href="/roadmap" className={styles.link}>
              Roadmap
            </Link>
            <Link href="/docs" className={styles.link}>
              Docs
            </Link>
          </div>

          <div className={styles.cta}>
            <Link href="/login" className={styles.login}>
              Log in
            </Link>
            <Button as={Link} href="/register" size="sm">
              Start free
            </Button>
            <MobileNav />
          </div>
        </nav>
      </Wrap>
    </header>
  );
}
