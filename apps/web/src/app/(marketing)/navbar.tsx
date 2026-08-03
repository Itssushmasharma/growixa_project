import Link from "next/link";
import { getCurrentUser } from "@/lib/auth";
import { BrandLogo } from "@/components/brand-logo";
import styles from "./marketing.module.css";

export async function Navbar() {
  const user = await getCurrentUser();

  return (
    <header className={styles.navbar}>
      <Link href="/" className={styles.brand}>
        <BrandLogo width={28} height={28} />
        <span>Growixa</span>
      </Link>

      <nav className={styles.navLinks}>
        <Link href="/features" className={styles.navLink}>
          Platform
        </Link>
        <Link href="/solutions" className={styles.navLink}>
          Solutions
        </Link>
        <Link href="/pricing" className={styles.navLink}>
          Pricing
        </Link>
        <Link href="/security" className={styles.navLink}>
          Security
        </Link>
        <Link href="/docs" className={styles.navLink}>
          Docs
        </Link>
      </nav>

      <div className={styles.navActions}>
        {user ? (
          <Link href="/dashboard" className={styles.primaryBtn}>
            Go to Dashboard
          </Link>
        ) : (
          <>
            <Link href="/login" className={styles.loginBtn}>
              Log In
            </Link>
            <Link href="/login" className={styles.primaryBtn}>
              Start Free
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
