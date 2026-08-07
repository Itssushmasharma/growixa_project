import { SupportSessionDetailPage } from "./support-session-detail-page";

export default async function PlatformSupportSessionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <SupportSessionDetailPage supportSessionId={id} />;
}
