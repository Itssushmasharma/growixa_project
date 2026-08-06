import { CampaignFormPage } from "../campaign-form-page";

export default async function CampaignDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <CampaignFormPage mode="edit" campaignId={id} />;
}
