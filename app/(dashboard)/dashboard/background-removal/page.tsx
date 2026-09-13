'use client';

import { useCallback, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Eraser, ImageUp, Loader2 } from 'lucide-react';

type Status = 'idle' | 'processing' | 'done' | 'error';

export default function BackgroundRemovalPage() {
  const [sourceUrl, setSourceUrl] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFile = useCallback((file: File) => {
    setResultUrl(null);
    setError(null);
    setStatus('idle');
    setSourceUrl(URL.createObjectURL(file));
  }, []);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) loadFile(file);
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) loadFile(file);
  };

  const removeBackgroundFromImage = async () => {
    if (!sourceUrl) return;
    setStatus('processing');
    setError(null);
    try {
      const { removeBackground } = await import('@imgly/background-removal');
      const blob = await removeBackground(sourceUrl);
      setResultUrl(URL.createObjectURL(blob));
      setStatus('done');
    } catch (err) {
      console.error(err);
      setError('تعذّرت معالجة الصورة. جرّب صورة أخرى.');
      setStatus('error');
    }
  };

  return (
    <section className="flex-1 p-4 lg:p-8">
      <h1 className="text-lg lg:text-2xl font-medium text-gray-900 mb-6">
        Background Removal
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Remove image background</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-300 p-10 text-center cursor-pointer hover:border-gray-400"
          >
            <ImageUp className="h-8 w-8 text-gray-400" />
            <p className="text-sm text-gray-600">
              Click to upload or drag and drop an image
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={onFileChange}
            />
          </div>

          {sourceUrl && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">
                  Original
                </p>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={sourceUrl}
                  alt="Original upload"
                  className="w-full rounded-lg border border-gray-200"
                />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">
                  Result
                </p>
                <div
                  className="w-full rounded-lg border border-gray-200 min-h-40 flex items-center justify-center bg-[length:16px_16px] bg-[image:repeating-conic-gradient(#e5e7eb_0_25%,#ffffff_0_50%)]"
                >
                  {status === 'processing' && (
                    <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                  )}
                  {resultUrl && status === 'done' && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={resultUrl}
                      alt="Background removed"
                      className="w-full rounded-lg"
                    />
                  )}
                  {status === 'idle' && (
                    <p className="text-sm text-gray-400 px-4">
                      Result will appear here
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              onClick={removeBackgroundFromImage}
              disabled={!sourceUrl || status === 'processing'}
              className="bg-orange-500 hover:bg-orange-600 text-white"
            >
              {status === 'processing' ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Eraser className="mr-2 h-4 w-4" />
                  Remove Background
                </>
              )}
            </Button>

            {resultUrl && status === 'done' && (
              <Button variant="outline" asChild>
                <a href={resultUrl} download="background-removed.png">
                  <Download className="mr-2 h-4 w-4" />
                  Download PNG
                </a>
              </Button>
            )}
          </div>

          <p className="text-xs text-gray-400">
            Processing happens entirely in your browser — images are never
            uploaded to a server.
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
