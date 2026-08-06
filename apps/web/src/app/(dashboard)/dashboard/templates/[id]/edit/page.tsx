import { TemplateFormPage } from "../../template-form-page";

export default async function EditTemplatePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TemplateFormPage mode="edit" templateId={id} />;
}
