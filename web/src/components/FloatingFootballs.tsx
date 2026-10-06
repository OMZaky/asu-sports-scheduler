"use client";

import { useEffect, useRef, useState } from "react";

interface Ball {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  sizeClass: string;
  rotation: number;
  rotSpeed: number;
}

export function FloatingFootballs() {
  const [mounted, setMounted] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const ballsRef = useRef<Ball[]>([]);
  const cursorRef = useRef({ x: -1000, y: -1000 });
  const animationRef = useRef<number>(0);

  useEffect(() => {
    const width = window.innerWidth;
    const height = window.innerHeight;

    // Approximate radii based on text sizes
    const allBalls = [
      { x: width * 0.2, y: height * 0.2, vx: 1, vy: 0.75, radius: 45, sizeClass: "text-7xl", rotation: 0, rotSpeed: 0.5 },
      { x: width * 0.8, y: height * 0.3, vx: -0.75, vy: 1, radius: 65, sizeClass: "text-9xl", rotation: 0, rotSpeed: -0.6 },
      { x: width * 0.5, y: height * 0.8, vx: -1, vy: -0.75, radius: 25, sizeClass: "text-5xl", rotation: 0, rotSpeed: 0.75 },
      { x: width * 0.1, y: height * 0.7, vx: 0.9, vy: -1, radius: 55, sizeClass: "text-8xl", rotation: 0, rotSpeed: -0.4 },
      { x: width * 0.7, y: height * 0.6, vx: -0.5, vy: -1.25, radius: 35, sizeClass: "text-6xl", rotation: 0, rotSpeed: 1 },
    ];
    
    // Reduce number of balls on mobile screens to prevent clutter
    ballsRef.current = width < 768 ? allBalls.slice(0, 3) : allBalls;

    setMounted(true);

    const handleMouseMove = (e: MouseEvent) => {
      cursorRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseLeave = () => {
      cursorRef.current = { x: -1000, y: -1000 };
    };

    window.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseleave", handleMouseLeave);

    const updatePhysics = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      const cursor = cursorRef.current;
      const cursorRadius = 120; // Distance at which cursor repels

      const balls = ballsRef.current;

      for (let i = 0; i < balls.length; i++) {
        const b = balls[i];

        b.x += b.vx;
        b.y += b.vy;
        b.rotation += b.rotSpeed;

        // Wall collisions (bounce)
        if (b.x < b.radius) { b.x = b.radius; b.vx *= -1; b.rotSpeed *= -1; }
        if (b.x > w - b.radius) { b.x = w - b.radius; b.vx *= -1; b.rotSpeed *= -1; }
        if (b.y < b.radius) { b.y = b.radius; b.vy *= -1; b.rotSpeed *= -1; }
        if (b.y > h - b.radius) { b.y = h - b.radius; b.vy *= -1; b.rotSpeed *= -1; }

        // Cursor repulsion
        const dx = b.x - cursor.x;
        const dy = b.y - cursor.y;
        const distSq = dx * dx + dy * dy;
        const minDist = b.radius + cursorRadius;

        if (distSq < minDist * minDist) {
          const dist = Math.sqrt(distSq);
          // Avoid division by zero
          if (dist > 0.1) {
            const force = (minDist - dist) / minDist;
            // Kick the ball away from cursor
            b.vx += (dx / dist) * force * 0.8;
            b.vy += (dy / dist) * force * 0.8;
            b.rotSpeed += (dx / dist) * force * 0.1; // Add minimal spin on touch
          }
        }

        // Clamp speed so they don't fly off too fast or stop completely
        const speed = Math.sqrt(b.vx * b.vx + b.vy * b.vy);
        const maxSpeed = 3.5;
        const minSpeed = 0.5;

        if (speed > maxSpeed) {
          b.vx = (b.vx / speed) * maxSpeed;
          b.vy = (b.vy / speed) * maxSpeed;
        } else if (speed < minSpeed && speed > 0.1) {
          b.vx *= 1.01;
          b.vy *= 1.01;
        }

        // Clamp rotation speed
        const maxRot = 1.0;
        if (b.rotSpeed > maxRot) b.rotSpeed = maxRot;
        if (b.rotSpeed < -maxRot) b.rotSpeed = -maxRot;
      }

      // Ball-to-ball collisions
      for (let i = 0; i < balls.length; i++) {
        for (let j = i + 1; j < balls.length; j++) {
          const b1 = balls[i];
          const b2 = balls[j];

          const dx = b2.x - b1.x;
          const dy = b2.y - b1.y;
          const distSq = dx * dx + dy * dy;
          const minDist = b1.radius + b2.radius;

          if (distSq < minDist * minDist) {
            const dist = Math.sqrt(distSq);
            if (dist === 0) continue;

            const nx = dx / dist;
            const ny = dy / dist;

            // Push them apart so they don't overlap
            const overlap = minDist - dist;
            b1.x -= nx * (overlap / 2);
            b1.y -= ny * (overlap / 2);
            b2.x += nx * (overlap / 2);
            b2.y += ny * (overlap / 2);

            // Calculate elastic collision velocities
            const kx = b1.vx - b2.vx;
            const ky = b1.vy - b2.vy;
            // p = dot product of relative velocity and normal
            const p = (nx * kx + ny * ky);

            b1.vx -= p * nx;
            b1.vy -= p * ny;
            b2.vx += p * nx;
            b2.vy += p * ny;

            // Reverse spin on hit
            b1.rotSpeed *= -1;
            b2.rotSpeed *= -1;
          }
        }
      }

      // Render directly to DOM for 60fps performance without React state overhead
      if (containerRef.current && containerRef.current.children.length === balls.length) {
        const children = containerRef.current.children;
        for (let i = 0; i < balls.length; i++) {
          const el = children[i] as HTMLElement;
          el.style.transform = `translate(${balls[i].x}px, ${balls[i].y}px) translate(-50%, -50%) rotate(${balls[i].rotation}deg)`;
        }
      }

      animationRef.current = requestAnimationFrame(updatePhysics);
    };

    animationRef.current = requestAnimationFrame(updatePhysics);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseleave", handleMouseLeave);
      cancelAnimationFrame(animationRef.current);
    };
  }, []);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
      <div ref={containerRef} className="absolute inset-0">
        {ballsRef.current.map((ball, i) => (
          <div
            key={i}
            className={`absolute top-0 left-0 ${ball.sizeClass} opacity-50 drop-shadow-2xl select-none`}
            style={{
              willChange: 'transform',
              transform: `translate(-1000px, -1000px)` // Hide off-screen until first physics frame
            }}
          >
            ⚽
          </div>
        ))}
      </div>
    </div>
  );
}
