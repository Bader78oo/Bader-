import 'server-only';
import { promises as fs } from 'fs';
import path from 'path';

// Shape of manifest.json written by pipeline/blender/process_model.py

export type TourLink = {
  to: string;
  yaw: number;
  pitch: number;
  distance: number;
};

export type TourPanorama = {
  id: string;
  file: string;
  kind: 'interior' | 'aerial';
  level: number | null;
  position: [number, number, number];
  links: TourLink[];
};

export type TourManifest = {
  version: number;
  source: string;
  units: 'm';
  unitScale: number;
  bounds: { min: number[]; max: number[] };
  model: { file: string; draco: boolean };
  levels: number;
  panoramas: TourPanorama[];
  stills: { id: string; file: string }[];
  processingSeconds: number;
};

const TOURS_DIR = path.join(process.cwd(), 'public', 'tours');

// Tours are served from /public/tours/<id>/ until processed output moves to object storage.
export function tourBaseUrl(id: string) {
  return `/tours/${id}`;
}

export async function getTourManifest(id: string): Promise<TourManifest | null> {
  if (!/^[a-z0-9-]+$/.test(id)) return null;
  try {
    const raw = await fs.readFile(path.join(TOURS_DIR, id, 'manifest.json'), 'utf8');
    return JSON.parse(raw) as TourManifest;
  } catch {
    return null;
  }
}
