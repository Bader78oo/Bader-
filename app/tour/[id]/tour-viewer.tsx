'use client';

import { useEffect, useRef, useState } from 'react';
import { Box, Images, Rotate3d } from 'lucide-react';
import type { TourManifest } from '@/lib/tours/manifest';
import '@photo-sphere-viewer/core/index.css';
import '@photo-sphere-viewer/markers-plugin/index.css';
import '@photo-sphere-viewer/virtual-tour-plugin/index.css';

type Mode = 'tour' | 'model' | 'stills';

function sceneName(manifest: TourManifest, id: string) {
  const pano = manifest.panoramas.find((p) => p.id === id);
  if (!pano) return id;
  if (pano.kind === 'aerial') return 'منظر جوي';
  const index = manifest.panoramas.filter((p) => p.kind === 'interior').indexOf(pano) + 1;
  return manifest.levels > 1 ? `الطابق ${(pano.level ?? 0) + 1} - مشهد ${index}` : `مشهد ${index}`;
}

function PanoramaTour({ manifest, baseUrl }: { manifest: TourManifest; baseUrl: string }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let viewer: { destroy(): void } | undefined;
    let cancelled = false;

    (async () => {
      const [{ Viewer }, { MarkersPlugin }, { VirtualTourPlugin }] = await Promise.all([
        import('@photo-sphere-viewer/core'),
        import('@photo-sphere-viewer/markers-plugin'),
        import('@photo-sphere-viewer/virtual-tour-plugin')
      ]);
      if (cancelled || !containerRef.current) return;

      const nodes = manifest.panoramas.map((p) => ({
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

      const start = manifest.panoramas.find((p) => p.kind !== 'aerial') ?? manifest.panoramas[0];
      viewer = new Viewer({
        container: containerRef.current,
        // Wide field of view, facing the way into the rest of the property
        defaultZoomLvl: 0,
        defaultYaw: start?.links[0]?.yaw ?? 0,
        defaultPitch: -0.1,
        loadingTxt: 'جارٍ التحميل...',
        navbar: ['zoom', 'move', 'caption', 'fullscreen'],
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
          ]
        ]
      });
    })();

    return () => {
      cancelled = true;
      viewer?.destroy();
    };
  }, [manifest, baseUrl]);

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

export function TourViewer({ manifest, baseUrl }: { manifest: TourManifest; baseUrl: string }) {
  const [mode, setMode] = useState<Mode>('tour');
  const tabs: { mode: Mode; label: string; icon: typeof Box; show: boolean }[] = [
    { mode: 'tour', label: 'جولة 360°', icon: Rotate3d, show: manifest.panoramas.length > 0 },
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
                onClick={() => setMode(m)}
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
        {mode === 'tour' && <PanoramaTour manifest={manifest} baseUrl={baseUrl} />}
        {mode === 'model' && <ModelView manifest={manifest} baseUrl={baseUrl} />}
        {mode === 'stills' && <Stills manifest={manifest} baseUrl={baseUrl} />}
      </main>
    </div>
  );
}
