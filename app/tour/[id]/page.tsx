import { notFound } from 'next/navigation';
import { getTourManifest, tourBaseUrl } from '@/lib/tours/manifest';
import { TourViewer } from './tour-viewer';

export default async function TourPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const manifest = await getTourManifest(id);
  if (!manifest) notFound();

  return <TourViewer manifest={manifest} baseUrl={tourBaseUrl(id)} />;
}
