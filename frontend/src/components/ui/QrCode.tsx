import { useEffect, useRef } from 'react';
import QRCodeLib from 'qrcode';

interface QrCodeProps {
  url: string;
  size?: number;
}

export default function QrCode({ url, size = 180 }: QrCodeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || !url) return;
    QRCodeLib.toCanvas(canvasRef.current, url, {
      width: size,
      margin: 2,
      color: { dark: '#5a7a7a', light: '#ffffff' },
    });
  }, [url, size]);

  if (!url) {
    return <div className="text-text-light text-sm">无法生成二维码</div>;
  }

  return <canvas ref={canvasRef} className="rounded-lg" />;
}
