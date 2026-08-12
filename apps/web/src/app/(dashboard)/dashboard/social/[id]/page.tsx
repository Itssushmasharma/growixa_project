import { PostFormPage } from "../post-form-page";

export default async function SocialPostDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <PostFormPage mode="edit" postId={id} />;
}
