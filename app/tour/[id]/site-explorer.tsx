'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Baby,
  Building2,
  Car,
  Dumbbell,
  Flame,
  Landmark,
  Map,
  Rotate3d,
  Sofa,
  Trees,
  Volleyball,
  Waves,
  type LucideIcon
} from 'lucide-react';
import type { AmenityType, SiteManifest } from '@/lib/tours/manifest';

const ICONS: Record<AmenityType, LucideIcon> = {
  tower: Building2,
  lobby: Sofa,
  pool: Waves,
  gym: Dumbbell,
  court: Volleyball,
  playground: Baby,
  bbq: Flame,
  garden: Trees,
  mosque: Landmark,
  parking: Car
};

const FADE_MS = 500;

/**
 * Navigate a compound by amenity: overview still, a bar of amenities, and pre-rendered fly
 * clips between them. Moving from amenity A to B plays A's fly-out (back to the overview) then
 * B's fly-in, so every pair of amenities is connected with only two clips per amenity.
 *
 * Layers, bottom to top: overview still (covers any gap between two clips, whose boundary frame
 * is the overview), video, current still (fades out once the video plays, back in when it ends).
 */
export function SiteExplorer({
  site,
  baseUrl,
  onOpen360
}: {
  site: SiteManifest;
  baseUrl: string;
  onOpen360: (panoId: string) => void;
}) {
  const url = useCallback((file: string) => `${baseUrl}/${file}`, [baseUrl]);
  const amenity = (id: string | null) => site.amenities.find((a) => a.id === id) ?? null;

  const [current, setCurrent] = useState<string | null>(null);
  // Destination while a transition is playing; undefined when idle
  const [target, setTarget] = useState<string | null | undefined>(undefined);
  const [queue, setQueue] = useState<string[]>([]);
  const [videoPlaying, setVideoPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const moving = target !== undefined;

  const currentStill = url(amenity(current)?.still ?? site.overview.still);
  const shown = amenity(moving ? target : current);

  const finish = useCallback(() => {
    setCurrent(target ?? null);
    setTarget(undefined);
    setQueue([]);
    // Let the new still fade in over the video's last frame before dropping the video
    setTimeout(() => setVideoPlaying(false), FADE_MS);
  }, [target]);

  const go = (dest: string | null) => {
    if (moving || dest === current) return;
    const clips: string[] = [];
    const from = amenity(current);
    const to = amenity(dest);
    if (from) clips.push(url(from.clipOut));
    if (to) clips.push(url(to.clipIn));
    setTarget(dest);
    setQueue(clips);
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video || queue.length === 0) return;
    const onPlaying = () => setVideoPlaying(true);
    video.addEventListener('playing', onPlaying, { once: true });
    video.src = queue[0];
    video.play().catch(() => finish());
    return () => video.removeEventListener('playing', onPlaying);
  }, [queue, finish]);

  const onEnded = () => {
    if (queue.length > 1) setQueue((q) => q.slice(1));
    else finish();
  };

  // Warm the cache so transitions start instantly: stills first, then clips
  useEffect(() => {
    const stills = site.amenities.map((a) => url(a.still));
    stills.forEach((src) => {
      const img = new Image();
      img.src = src;
    });
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      for (const a of site.amenities) {
        for (const clip of [a.clipIn, a.clipOut]) {
          try {
            await fetch(url(clip), { signal: controller.signal, priority: 'low' } as RequestInit);
          } catch {
            return;
          }
        }
      }
    }, 1000);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [site, url]);

  const stillVisible = !moving || !videoPlaying;

  return (
    <div className="relative h-full w-full overflow-hidden bg-black">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={url(site.overview.still)} alt="" className="absolute inset-0 h-full w-full object-cover" />
      <video
        ref={videoRef}
        muted
        playsInline
        preload="auto"
        onEnded={onEnded}
        className={`absolute inset-0 h-full w-full object-cover ${videoPlaying ? 'opacity-100' : 'opacity-0'}`}
      />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        key={currentStill}
        src={currentStill}
        alt={shown?.name.ar ?? 'المشروع'}
        className="absolute inset-0 h-full w-full object-cover transition-opacity"
        style={{ opacity: stillVisible ? 1 : 0, transitionDuration: `${FADE_MS}ms` }}
      />

      <div dir="rtl" className="pointer-events-none absolute inset-x-0 top-0 bg-gradient-to-b from-black/60 to-transparent p-5 pb-16">
        <h2 className="text-2xl font-bold text-white drop-shadow sm:text-3xl">{shown?.name.ar ?? 'نظرة عامة على المشروع'}</h2>
        <p className="mt-1 text-sm text-white/80">{shown ? shown.name.en : 'Project overview'}</p>
      </div>

      {current && !moving && (
        <button
          onClick={() => onOpen360(amenity(current)!.pano)}
          className="absolute left-4 top-5 flex items-center gap-2 rounded-full bg-white/90 px-4 py-2 text-sm font-medium text-gray-900 shadow-lg transition hover:bg-white"
        >
          <Rotate3d className="h-4 w-4" />
          جولة 360°
        </button>
      )}

      <nav dir="rtl" className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent px-3 pb-4 pt-10">
        <div className="mx-auto flex max-w-5xl gap-2 overflow-x-auto rounded-2xl bg-black/50 p-2 backdrop-blur [scrollbar-width:none]">
          {[{ id: null, name: { ar: 'نظرة عامة' }, Icon: Map }, ...site.amenities.map((a) => ({ id: a.id, name: a.name, Icon: ICONS[a.type] ?? Building2 }))].map(
            ({ id, name, Icon }) => {
              const active = (moving ? target : current) === id;
              return (
                <button
                  key={id ?? 'overview'}
                  onClick={() => go(id)}
                  disabled={moving}
                  className={`flex min-w-[76px] shrink-0 flex-col items-center gap-1 rounded-xl px-3 py-2 text-xs transition-colors ${
                    active ? 'bg-orange-500 text-white' : 'text-white/80 hover:bg-white/10 hover:text-white'
                  } disabled:cursor-wait`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="whitespace-nowrap">{name.ar}</span>
                </button>
              );
            }
          )}
        </div>
      </nav>
    </div>
  );
}
