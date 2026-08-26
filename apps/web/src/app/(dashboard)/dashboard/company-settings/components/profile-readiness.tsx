import type { BrandProfile, CompanyProfile } from "../types";
import styles from "./components.module.css";

const READINESS_CHECKS: Array<
  (company: CompanyProfile | null, brand: BrandProfile | null) => boolean
> = [
  (company) => Boolean(company?.name),
  (company) => Boolean(company?.website),
  (company) => Boolean(company?.industry),
  (company) => Boolean(company?.business_address),
  (company) => Boolean(company?.support_email),
  (company) => Boolean(company?.description),
  (company) => Boolean(company?.logo_url),
  (_company, brand) => Boolean(brand?.brand_voice),
  (_company, brand) => Boolean(brand && brand.persona_tags.length > 0),
  (_company, brand) => Boolean(brand && brand.forbidden_claims.length > 0),
];

export function computeReadinessPercent(
  company: CompanyProfile | null,
  brand: BrandProfile | null,
): number {
  if (!company) return 0;
  const passed = READINESS_CHECKS.filter((check) => check(company, brand)).length;
  return Math.round((passed / READINESS_CHECKS.length) * 100);
}

function mostRecentUpdate(
  company: CompanyProfile | null,
  brand: BrandProfile | null,
): string | null {
  const timestamps = [company?.updated_at, brand?.updated_at].filter((value): value is string =>
    Boolean(value),
  );
  if (timestamps.length === 0) return null;
  return timestamps.sort().at(-1) ?? null;
}

interface ProfileReadinessProps {
  company: CompanyProfile | null;
  brand: BrandProfile | null;
}

export function ProfileReadiness({ company, brand }: ProfileReadinessProps) {
  const percent = computeReadinessPercent(company, brand);
  const lastUpdated = mostRecentUpdate(company, brand);

  return (
    <div className={styles.readinessWrap}>
      <span className={styles.readinessBadge}>{percent}% Ready</span>
      {lastUpdated && (
        <span className={styles.readinessMeta}>
          Updated{" "}
          {new Date(lastUpdated).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
          })}
        </span>
      )}
    </div>
  );
}
