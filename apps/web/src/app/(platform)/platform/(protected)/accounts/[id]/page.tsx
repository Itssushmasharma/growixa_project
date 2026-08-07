import { AccountDetailPage } from "./account-detail-page";

export default async function PlatformAccountDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <AccountDetailPage accountId={id} />;
}
