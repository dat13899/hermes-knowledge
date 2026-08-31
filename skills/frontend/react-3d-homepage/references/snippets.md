# 3D Homepage — Code Snippets & Patterns

## Scene3D: Floating Torus Knot

```jsx
import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, MeshDistortMaterial } from '@react-three/drei';

function FloatingTorus({ color = '#34d399', position = [0, 0, 0], scale = 1, speed = 0.5 }) {
  const ref = useRef();
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.x = clock.getElapsedTime() * 0.2 * speed;
      ref.current.rotation.y = clock.getElapsedTime() * 0.3 * speed;
    }
  });
  return (
    <Float speed={1.5} rotationIntensity={0.4} floatIntensity={0.6}>
      <mesh ref={ref} position={position} scale={scale}>
        <torusKnotGeometry args={[1, 0.3, 100, 16]} />
        <MeshDistortMaterial color={color} transparent opacity={0.08} wireframe distort={0.15} speed={2} />
      </mesh>
    </Float>
  );
}
```

## Scene3D: Instanced Particle Field

```jsx
function ParticleField({ count = 400 }) {
  const mesh = useRef();
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 12;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 8;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 6;
    }
    return pos;
  }, [count]);

  useFrame(({ clock }) => {
    if (mesh.current) {
      mesh.current.rotation.y = clock.getElapsedTime() * 0.03;
    }
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.015} color="#34d399" transparent opacity={0.4} depthWrite={false} />
    </points>
  );
}
```

## NeuralNodes: Service Node Card

```jsx
<motion.div
  initial={{ opacity: 0, scale: 0.8 }}
  animate={inView ? { opacity: 1, scale: 1 } : {}}
  transition={{ delay: 0.08 * i, duration: 0.4 }}
  style={{
    background: svc.status === 'running' ? 'rgba(34,197,94,0.08)' : 'rgba(107,114,128,0.06)',
    border: `1px solid ${svc.status === 'running' ? 'rgba(34,197,94,0.2)' : 'rgba(107,114,128,0.12)'}`,
    borderRadius: 'var(--radius-md)', padding: '1rem',
    cursor: 'pointer', position: 'relative', overflow: 'hidden',
    backdropFilter: 'blur(8px)',
  }}
  whileHover={{ scale: 1.02, borderColor: 'rgba(52,211,153,0.3)' }}
  whileTap={{ scale: 0.98 }}
  onClick={() => onToggle?.(svc, svc.status === 'running' ? 'stop' : 'start')}
>
  {/* Pulse ring for running services */}
  {svc.status === 'running' && (
    <div style={{
      position: 'absolute', top: 8, right: 8,
      width: 10, height: 10, borderRadius: '50%',
      background: '#22c55e',
      boxShadow: '0 0 8px rgba(34,197,94,0.5), 0 0 16px rgba(34,197,94,0.2)',
      animation: 'aiPulse 2s ease-in-out infinite',
    }} />
  )}
  {/* Content */}
</motion.div>
```

## Terminal: Sequential Typing State Machine

```jsx
const [visibleLines, setVisibleLines] = useState([]);
const [currentCmd, setCurrentCmd] = useState(0);
const [typing, setTyping] = useState('');
const [charIdx, setCharIdx] = useState(0);
const [showOutput, setShowOutput] = useState(false);

useEffect(() => {
  if (currentCmd >= COMMANDS.length) return;
  const cmd = COMMANDS[currentCmd];
  if (charIdx < cmd.input.length) {
    const t = setTimeout(() => { setTyping(cmd.input.slice(0, charIdx + 1)); setCharIdx(c => c + 1); }, 50);
    return () => clearTimeout(t);
  }
  if (!showOutput) {
    const t = setTimeout(() => setShowOutput(true), 300);
    return () => clearTimeout(t);
  }
  const t = setTimeout(() => {
    setVisibleLines(v => [...v, currentCmd]);
    setCurrentCmd(c => c + 1); setTyping(''); setCharIdx(0); setShowOutput(false);
  }, 500);
  return () => clearTimeout(t);
}, [currentCmd, charIdx, showOutput]);
```

## Lenis Integration (React 19 safe)

```jsx
useEffect(() => {
  let lenis;
  import('lenis').then(mod => {
    const Lenis = mod.default;
    lenis = new Lenis({
      lerp: isMobile ? 0.1 : 0.065,
      wheelMultiplier: 1,
      smoothWheel: true,
      syncTouch: true,
    });
    const raf = (time) => { lenis.raf(time); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  });
  return () => lenis?.destroy();
}, [isMobile]);
```

## Shimmer CSS Keyframe

```css
@keyframes shimmer {
  0% { background-position: 200% center; }
  100% { background-position: -200% center; }
}
```

## Build Output Sizes (reference)

| Chunk | Size | Content |
|-------|------|---------|
| HomePage | ~900KB (gzip 250KB) | Three.js engine + 3D scene + all sections |
| index | ~385KB (gzip 124KB) | React + Motion + shared libs |
| lenis | ~19KB (gzip 5.6KB) | Smooth scroll engine |
| DocumentsPage | ~40KB (gzip 10.8KB) | Document viewer |
| DashboardPage | ~15KB (gzip 4.6KB) | Service dashboard |
