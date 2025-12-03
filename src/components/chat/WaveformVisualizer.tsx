import React, { useRef, useEffect } from "react";

interface WaveformVisualizerProps {
  volumeLevel: number;
  isActive: boolean;
  width?: number;
  height?: number;
  barCount?: number;
  barColor?: string;
  barGap?: number;
}

/**
 * Real-time waveform visualizer that reacts to voice volume
 */
export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  volumeLevel,
  isActive,
  width = 200,
  height = 40,
  barCount = 20,
  barColor = "#3b82f6",
  barGap = 2,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const barsRef = useRef<number[]>(Array(barCount).fill(0));
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas dimensions
    canvas.width = width;
    canvas.height = height;

    const barWidth = (width - barGap * (barCount - 1)) / barCount;
    const centerY = height / 2;

    const draw = () => {
      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      if (!isActive) {
        // Draw flat line when inactive
        barsRef.current = barsRef.current.map((bar) => bar * 0.8); // Smooth decay
      } else {
        // Update bars based on volume level
        barsRef.current = barsRef.current.map((bar, index) => {
          // Generate semi-random heights based on volume
          const randomFactor = Math.random() * 0.5 + 0.5;
          const targetHeight = volumeLevel * randomFactor * height * 0.8;

          // Smooth transition
          const smoothedHeight = bar + (targetHeight - bar) * 0.3;
          return smoothedHeight;
        });
      }

      // Draw bars
      barsRef.current.forEach((barHeight, index) => {
        const x = index * (barWidth + barGap);
        const y = centerY - barHeight / 2;
        const h = Math.max(barHeight, 2); // Minimum bar height

        // Gradient for visual effect
        const gradient = ctx.createLinearGradient(x, y, x, y + h);
        gradient.addColorStop(0, barColor);
        gradient.addColorStop(1, barColor + "80"); // Add transparency

        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth, h);
      });

      animationFrameRef.current = requestAnimationFrame(draw);
    };

    draw();

    // Cleanup
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [volumeLevel, isActive, width, height, barCount, barColor, barGap]);

  return (
    <canvas
      ref={canvasRef}
      className="rounded-md"
      style={{ width: `${width}px`, height: `${height}px` }}
    />
  );
};

export default WaveformVisualizer;
