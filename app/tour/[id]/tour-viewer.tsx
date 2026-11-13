'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Box, Images, Map, Rotate3d, X } from 'lucide-react';
import type { PluginConstructor } from '@photo-sphere-viewer/core';
import type { TourManifest, TourPanorama } from '@/lib/tours/manifest';
import { SiteExplorer, type AutoPlay } from './site-explorer';
import '@photo-sphere-viewer/core/index.css';
import '@photo-sphere-viewer/markers-plugin/index.css';
import '@photo-sphere-viewer/virtual-tour-plugin/index.css';

type Mode = 'site' | 'tour' | 'model' | 'stills';

function sceneName(manifest: TourManifest, id: string) {
  const pano = manifest.panoramas.find((p) => p.id === id);
  if (!pano) return id;
  if (pano.kind === 'aerial') return 'منظر جوي';
  if (pano.kind === 'amenity') {
    return manifest.site?.amenities.find((a) => a.pano === id)?.name.ar ?? id;
  }
  const index = manifest.panoramas.filter((p) => p.kind === 'interior').indexOf(pano) + 1;
  return manifest.levels > 1 ? `الطابق ${(pano.level ?? 0) + 1} - مشهد ${index}` : `مشهد ${index}`;
}

function PanoramaTour({
  manifest,
  panoramas,
  startId,
  baseUrl,
  autoRotate = false
}: {
  manifest: TourManifest;
  panoramas: TourPanorama[];
  startId?: string;
  baseUrl: string;
  /** Unattended display: turn slowly on its own and drop the controls nobody can press */
  autoRotate?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let viewer: { destroy(): void } | undefined;
    let cancelled = false;

    (async () => {
      const [{ Viewer }, { MarkersPlugin }, { VirtualTourPlugin }, autorotate] = await Promise.all([
        import('@photo-sphere-viewer/core'),
        import('@photo-sphere-viewer/markers-plugin'),
        import('@photo-sphere-viewer/virtual-tour-plugin'),
        autoRotate ? import('@photo-sphere-viewer/autorotate-plugin') : Promise.resolve(null)
      ]);
      if (cancelled || !containerRef.current) return;

      const nodes = panoramas.map((p) => ({
        id: p.id,
        panorama: `${baseUrl}/${p.file}`,
        name: sceneName(manifest, p.id),
        caption: sceneName(manifest, p.id),
        thumbnail: `${baseUrl}/${p.file}`,
        links: p.links.map((l) => ({
          nodeId: l.to,
          position: { yaw: l.yaw, pitch: l.pitch }
        }))
      }));

      const start =
        panoramas.find((p) => p.id === startId) ?? panoramas.find((p) => p.kind !== 'aerial') ?? panoramas[0];
      viewer = new Viewer({
        container: containerRef.current,
        // Wide field of view, facing the way into the rest of the property
        defaultZoomLvl: 0,
        defaultYaw: start?.heading ?? start?.links[0]?.yaw ?? 0,
        defaultPitch: -0.1,
        loadingTxt: 'جارٍ التحميل...',
        navbar: autoRotate ? false : ['zoom', 'move', 'caption', 'fullscreen'],
        plugins: [
          MarkersPlugin,
          [
            VirtualTourPlugin,
            {
              positionMode: 'manual',
              renderMode: '3d',
              nodes,
              startNodeId: start?.id
            }
          ],
          ...((autorotate
            ? [[autorotate.AutorotatePlugin, { autostartDelay: 500, autostartOnIdle: true, autorotateSpeed: '1rpm' }]]
            : []) as [PluginConstructor, unknown][])
        ]
      });
    })();

    return () => {
      cancelled = true;
      viewer?.destroy();
    };
  }, [manifest, panoramas, startId, baseUrl, autoRotate]);

  return <div ref={containerRef} className="h-full w-full" />;
}

function ModelView({ manifest, baseUrl }: { manifest: TourManifest; baseUrl: string }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    import('@google/model-viewer').then(() => setReady(true));
  }, []);

  if (!ready) {
    return <div className="flex h-full items-center justify-center text-gray-400">جارٍ التحميل...</div>;
  }
  return (
    <model-viewer
      src={`${baseUrl}/${manifest.model.file}`}
      camera-controls
      auto-rotate
      shadow-intensity="1"
      exposure="1"
      camera-orbit="45deg 60deg auto"
      style={{ width: '100%', height: '100%', background: '#111827' }}
    />
  );
}

function Stills({ manifest, baseUrl }: { manifest: TourManifest; baseUrl: string }) {
  return (
    <div className="grid h-full auto-rows-min grid-cols-1 gap-4 overflow-y-auto p-4 sm:grid-cols-2">
      {manifest.stills.map((s) => (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          key={s.id}
          src={`${baseUrl}/${s.file}`}
          alt="منظر خارجي للمشروع"
          className="w-full rounded-lg"
        />
      ))}
    </div>
  );
}

/** How long each stop holds on an unattended wall screen */
export type DisplayTiming = { stillMs: number; panoMs: number };

export function TourViewer({
  manifest,
  baseUrl,
  display = null
}: {
  manifest: TourManifest;
  baseUrl: string;
  /** Set for an unattended screen: no controls, walks itself, never stops */
  display?: DisplayTiming | null;
}) {
  const site = manifest.site?.amenities.length ? manifest.site : null;
  const [mode, setMode] = useState<Mode>(site ? 'site' : 'tour');
  // Amenity 360 opened from the site view, shown as an overlay
  const [amenityPano, setAmenityPano] = useState<string | null>(null);
  const tourPanoramas = useMemo(() => manifest.panoramas.filter((p) => p.kind !== 'amenity'), [manifest]);
  const overlayPanoramas = useMemo(
    () => manifest.panoramas.filter((p) => p.id === amenityPano),
    [manifest, amenityPano]
  );

  const auto = useMemo<AutoPlay | null>(
    () => (display ? { ...display, paused: amenityPano !== null } : null),
    [display, amenityPano]
  );

  // Close the 360 leg and let the walk carry on
  useEffect(() => {
    if (!display || !amenityPano || display.panoMs <= 0) return;
    const timer = setTimeout(() => setAmenityPano(null), display.panoMs);
    return () => clearTimeout(timer);
  }, [display, amenityPano]);

  // A screen in a lobby must not sleep. Ignored where the browser has no wake lock.
  useEffect(() => {
    if (!display) return;
    type Lock = { release(): Promise<void> };
    const wakeLock = (navigator as Navigator & { wakeLock?: { request(t: 'screen'): Promise<Lock> } }).wakeLock;
    if (!wakeLock) return;
    let lock: Lock | null = null;
    const acquire = () => {
      wakeLock
        .request('screen')
        .then((l) => {
          lock = l;
        })
        .catch(() => {});
    };
    acquire();
    const onVisible = () => document.visibilityState === 'visible' && acquire();
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      document.removeEventListener('visibilitychange', onVisible);
      lock?.release().catch(() => {});
    };
  }, [display]);

  // With no amenities to walk there is still something to show: step through the 360s instead
  const [panoStep, setPanoStep] = useState(0);
  useEffect(() => {
    if (!display || site || tourPanoramas.length < 2) return;
    const every = display.panoMs > 0 ? display.panoMs : 15000;
    const timer = setInterval(() => setPanoStep((i) => (i + 1) % tourPanoramas.length), every);
    return () => clearInterval(timer);
  }, [display, site, tourPanoramas]);

  if (display) {
    const standby = tourPanoramas[panoStep % Math.max(tourPanoramas.length, 1)];
    return (
      <div dir="rtl" className="h-[100dvh] w-full cursor-none overflow-hidden bg-black text-white">
        <main dir="ltr" className="relative h-full w-full">
          {site ? (
            <SiteExplorer site={site} baseUrl={baseUrl} onOpen360={setAmenityPano} auto={auto} />
          ) : standby ? (
            <PanoramaTour
              key={standby.id}
              manifest={manifest}
              panoramas={tourPanoramas}
              startId={standby.id}
              baseUrl={baseUrl}
              autoRotate
            />
          ) : (
            <ModelView manifest={manifest} baseUrl={baseUrl} />
          )}
          {amenityPano && (
            <div className="absolute inset-0 z-20 bg-black">
              <PanoramaTour manifest={manifest} panoramas={overlayPanoramas} baseUrl={baseUrl} autoRotate />
            </div>
          )}
        </main>
      </div>
    );
  }
  const tabs: { mode: Mode; label: string; icon: typeof Box; show: boolean }[] = [
    { mode: 'site', label: 'المشروع', icon: Map, show: !!site },
    { mode: 'tour', label: 'جولة 360°', icon: Rotate3d, show: tourPanoramas.length > 0 },
    { mode: 'model', label: 'نموذج ثلاثي الأبعاد', icon: Box, show: true },
    { mode: 'stills', label: 'صور خارجية', icon: Images, show: manifest.stills.length > 0 }
  ];

  return (
    <div dir="rtl" className="flex h-[100dvh] flex-col bg-gray-900 text-white">
      <header className="flex items-center justify-between gap-2 px-4 py-3">
        <h1 className="truncate text-lg font-semibold">جولة افتراضية</h1>
        <nav className="flex gap-1 rounded-full bg-gray-800 p-1">
          {tabs
            .filter((t) => t.show)
            .map(({ mode: m, label, icon: Icon }) => (
              <button
                key={m}
                onClick={() => {
                  setMode(m);
                  setAmenityPano(null);
                }}
                className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm transition-colors ${
                  mode === m ? 'bg-orange-500 text-white' : 'text-gray-300 hover:text-white'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
        </nav>
      </header>
      <main dir="ltr" className="relative min-h-0 flex-1">
        {mode === 'site' && site && <SiteExplorer site={site} baseUrl={baseUrl} onOpen360={setAmenityPano} />}
        {mode === 'tour' && <PanoramaTour manifest={manifest} panoramas={tourPanoramas} baseUrl={baseUrl} />}
        {mode === 'model' && <ModelView manifest={manifest} baseUrl={baseUrl} />}
        {mode === 'stills' && <Stills manifest={manifest} baseUrl={baseUrl} />}
        {amenityPano && (
          <div className="absolute inset-0 z-20 bg-black">
            <PanoramaTour manifest={manifest} panoramas={overlayPanoramas} baseUrl={baseUrl} />
            <button
              onClick={() => setAmenityPano(null)}
              aria-label="إغلاق"
              className="absolute right-4 top-4 z-10 rounded-full bg-white/90 p-2 text-gray-900 shadow-lg hover:bg-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
