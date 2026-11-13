import { notFound } from 'next/navigation';
import { getTourManifest, tourBaseUrl } from '@/lib/tours/manifest';
import { TourViewer } from './tour-viewer';

type Query = { [key: string]: string | string[] | undefined };

const first = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);

/** `?dwell=8` → 8000 ms, clamped to two minutes; anything unparseable keeps the default */
function ms(value: string | string[] | undefined, fallbackSeconds: number) {
  const seconds = Number(first(value));
  const use = Number.isFinite(seconds) && seconds >= 0 ? Math.min(seconds, 120) : fallbackSeconds;
  return Math.round(use * 1000);
}

/**
 * `/tour/<id>` is the interactive viewer.
 *
 * `/tour/<id>?display=1` is the unattended one, for a screen on a wall with nothing to tap:
 * no controls, it walks the amenities by itself and loops forever. `?dwell=` sets how long each
 * stop holds (default 7s) and `?pano=` how long its 360 turns (default 12s, `0` to skip the 360s).
 */
export default async function TourPage({
  params,
  searchParams
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Query>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const manifest = await getTourManifest(id);
  if (!manifest) notFound();

  const flag = first(query.display) ?? first(query.kiosk);
  const display = flag !== undefined && flag !== '0' && flag !== 'false';

  return (
    <TourViewer
      manifest={manifest}
      baseUrl={tourBaseUrl(id)}
      display={display ? { stillMs: ms(query.dwell, 7), panoMs: ms(query.pano, 12) } : null}
    />
  );
}
