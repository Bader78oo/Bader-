'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Accessibility,
  Activity,
  Ambulance,
  Baby,
  BedDouble,
  Blocks,
  Building2,
  Car,
  Droplets,
  Dumbbell,
  Flame,
  HeartPulse,
  Landmark,
  Map,
  Microscope,
  Pill,
  Plane,
  Presentation,
  Ribbon,
  Rotate3d,
  Scan,
  Sofa,
  Stethoscope,
  Syringe,
  Trees,
  UtensilsCrossed,
  Volleyball,
  Waves,
  type LucideIcon
} from 'lucide-react';
import type { AmenityType, SiteManifest } from '@/lib/tours/manifest';

const ICONS: Record<AmenityType, LucideIcon> = {
  tower: Building2,
  lobby: Sofa,
  emergency: Ambulance,
  clinic: Stethoscope,
  radiology: Scan,
  lab: Microscope,
  pharmacy: Pill,
  surgery: Syringe,
  icu: Activity,
  maternity: Baby,
  ward: BedDouble,
  dialysis: Droplets,
  cardiology: HeartPulse,
  oncology: Ribbon,
  pediatrics: Blocks,
  physio: Accessibility,
  auditorium: Presentation,
  cafeteria: UtensilsCrossed,
  helipad: Plane,
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

/** Unattended display: walk the amenities on a loop instead of waiting for a tap. */
export type AutoPlay = {
  /** How long a hero still stays on screen before moving on */
  stillMs: number;
  /** How long the amenity's 360 is shown, slowly rotating; 0 skips the 360 */
  panoMs: number;
  /** True while the 360 overlay is up, so the walk waits for it */
  paused: boolean;
};

/**
 * Navigate a compound by amenity: overview still, a bar of amenities, and pre-rendered fly
 * clips between them. Moving from amenity A to B plays A's fly-out (back to the overview) then
 * B's fly-in, so every pair of amenities is connected with only two clips per amenity.
 *
 * Layers, bottom to top: overview still (covers any gap between two clips, whose boundary frame
 * is the overview), video, current still (fades out once the video plays, back in when it ends).
 *
 * With `auto` set the same machine runs unattended on a wall screen: no controls are drawn and
 * the walk steps overview → amenity → amenity → ... → overview for as long as the page is open.
 */
export function SiteExplorer({
  site,
  baseUrl,
  onOpen360,
  auto
}: {
  site: SiteManifest;
  baseUrl: string;
  onOpen360: (panoId: string) => void;
  auto?: AutoPlay | null;
}) {
  const url = useCallback((file: string) => `${baseUrl}/${file}`, [baseUrl]);
  const amenities = site.amenities;
  const amenity = useCallback(
    (id: string | null) => amenities.find((a) => a.id === id) ?? null,
    [amenities]
  );

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

  const go = useCallback(
    (dest: string | null) => {
      if (moving || dest === current) return;
      const clips: string[] = [];
      const from = amenity(current);
      const to = amenity(dest);
      if (from) clips.push(url(from.clipOut));
      if (to) clips.push(url(to.clipIn));
      setTarget(dest);
      setQueue(clips);
    },
    [moving, current, amenity, url]
  );

  useEffect(() => {
    const video = videoRef.current;
    if (!video || queue.length === 0) return;
    const onPlaying = () => setVideoPlaying(true);
    video.addEventListener('playing', onPlaying, { once: true });
    video.src = queue[0];
    video.play().catch(() => finish());
    return () => video.removeEventListener('playing', onPlaying);
  }, [queue, finish]);

  const step = useCallback(() => {
    if (queue.length > 1) setQueue((q) => q.slice(1));
    else finish();
  }, [queue.length, finish]);

  // A screen nobody attends must never freeze on a clip that stalls mid-download: every clip gets
  // a deadline a little past its own length, after which the walk carries on without it.
  useEffect(() => {
    if (!auto || queue.length === 0) return;
    const deadline = setTimeout(() => step(), (site.clip.seconds + 4) * 1000);
    return () => clearTimeout(deadline);
  }, [auto, queue, step, site.clip.seconds]);

  // Unattended walk. Each stop: hold the still, show its 360 once, then fly to the next amenity.
  const panoShownFor = useRef<string | null>(null);
  useEffect(() => {
    if (!auto || auto.paused || moving || amenities.length === 0) return;
    const timer = setTimeout(() => {
      const stop = amenity(current);
      if (stop && auto.panoMs > 0 && panoShownFor.current !== stop.id) {
        panoShownFor.current = stop.id;
        onOpen360(stop.pano);
        return;
      }
      const walk: (string | null)[] = [null, ...amenities.map((a) => a.id)];
      const next = walk[(walk.indexOf(current) + 1) % walk.length];
      go(next);
    }, auto.stillMs);
    return () => clearTimeout(timer);
  }, [auto, moving, current, amenities, amenity, go, onOpen360]);

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
        onEnded={step}
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

      <div
        dir="rtl"
        className={`pointer-events-none absolute inset-x-0 top-0 bg-gradient-to-b from-black/60 to-transparent ${
          auto ? 'p-10 pb-24' : 'p-5 pb-16'
        }`}
      >
        <h2
          className={`font-bold text-white drop-shadow ${
            auto ? 'text-5xl leading-tight 2xl:text-7xl' : 'text-2xl sm:text-3xl'
          }`}
        >
          {shown?.name.ar ?? 'نظرة عامة على المشروع'}
        </h2>
        <p className={`text-white/80 ${auto ? 'mt-3 text-2xl 2xl:text-3xl' : 'mt-1 text-sm'}`}>
          {shown ? shown.name.en : 'Project overview'}
        </p>
      </div>

      {current && !moving && !auto && (
        <button
          onClick={() => onOpen360(amenity(current)!.pano)}
          className="absolute left-4 top-5 flex items-center gap-2 rounded-full bg-white/90 px-4 py-2 text-sm font-medium text-gray-900 shadow-lg transition hover:bg-white"
        >
          <Rotate3d className="h-4 w-4" />
          جولة 360°
        </button>
      )}

      {!auto && (
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
      )}

      {/* Wall-screen footer: which stop we are on, legible from across a lobby */}
      {auto && amenities.length > 0 && (
        <div dir="rtl" className="absolute inset-x-0 bottom-0 flex justify-center gap-3 bg-gradient-to-t from-black/70 to-transparent px-10 pb-10 pt-20">
          {[null, ...amenities.map((a) => a.id)].map((id) => (
            <span
              key={id ?? 'overview'}
              className={`h-2.5 rounded-full transition-all duration-500 ${
                (moving ? target : current) === id ? 'w-12 bg-orange-500' : 'w-2.5 bg-white/40'
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
