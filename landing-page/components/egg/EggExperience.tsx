'use client';
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { EGG_COUNT, EGG_COLORS, collectEgg } from './game';

export default function EggExperience({children}: {children: ReactNode}) {
  const mount = useRef<HTMLDivElement>(null);
  const meadow = useRef<HTMLElement>(null);
  const api = useRef<{collect: (id: number) => void; reset: () => void; dispose: () => void} | null>(null);
  const ids = useRef<number[]>([]);
  const [collected, setCollected] = useState<number[]>([]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'fallback'>('loading');
  const [reduced, setReduced] = useState(false);
  const [showList, setShowList] = useState(false);
  const [message, setMessage] = useState('');
  const complete = collected.length === EGG_COUNT;

  useEffect(() => {
    let cancelled = false;
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(media.matches);
    const update = () => setReduced(media.matches);
    media.addEventListener('change', update);
    import('./scene').then(({createEggScene}) => {
      if (cancelled || !mount.current || !meadow.current) return;
      api.current = createEggScene(mount.current, meadow.current, {
        onCollect(id) {
          const next = collectEgg(ids.current, id);
          if (next.length === ids.current.length) return;
          ids.current = next;
          setCollected(next);
          setMessage(next.length === EGG_COUNT ? 'All accounted for. Every egg is in the basket.' : `In the basket. ${next.length} of ${EGG_COUNT} eggs collected.`);
        },
        onError() {setStatus('fallback'); setShowList(true);},
      });
      setStatus('ready');
    }).catch(() => { if (!cancelled) {setStatus('fallback'); setShowList(true);} });
    return () => { cancelled = true; media.removeEventListener('change', update); api.current?.dispose(); api.current = null; };
  }, []);

  function collect(id: number) {
    if (api.current && status === 'ready') api.current.collect(id);
    else {
      const next = collectEgg(ids.current, id);
      ids.current = next; setCollected(next);
      setMessage(next.length === EGG_COUNT ? 'All accounted for.' : `In the basket. ${next.length} of ${EGG_COUNT}.`);
    }
  }
  function replay() { ids.current = []; setCollected([]); setMessage('A fresh basket. Find all 18 eggs.'); api.current?.reset(); }
  return <div className={`egg-experience ${status === 'fallback' ? 'scene-fallback' : ''}`}>
    <div ref={mount} className="egg-canvas" aria-hidden="true" />
    {status === 'loading' && <div className="scene-loading" role="status">Waking up the eggs…</div>}
    {children}
    <section ref={meadow} id="meadow" className="meadow" aria-labelledby="meadow-title">
      <div className="meadow-top"><div><span className="section-label">ONE LAST THING</span><h2 id="meadow-title">You dropped these.</h2><p>{status === 'fallback' ? 'The 3D meadow couldn’t load. You can still collect every egg below.' : 'Click or tap an egg. We’ll keep it for you.'}</p></div><div className="egg-counter"><span>IN THE BASKET</span><strong>{String(collected.length).padStart(2,'0')}<i> / {EGG_COUNT}</i></strong></div></div>
      <div className="meadow-space" aria-label="3D meadow with 18 collectible eggs" />
      <div className="meadow-bottom"><div><strong>{complete ? 'All accounted for.' : 'No rush. Nothing gets lost here.'}</strong><p>{complete ? 'Every egg you dropped is back in the basket.' : 'Find all 18. Put them where they belong.'}</p></div><div className="meadow-actions"><button onClick={() => setShowList(!showList)} aria-expanded={showList} aria-controls="egg-list">{showList ? 'HIDE EGG LIST' : 'COLLECT WITH KEYBOARD'}</button><button onClick={replay}>PLAY AGAIN ↺</button><a href="#early-access">EARLY ACCESS ↗</a></div></div>
      <div className="sr-only" role="status" aria-live="polite">{message}</div>
      {showList && <div id="egg-list" className="egg-list"><p>{reduced ? 'Reduced motion is on. ' : ''}Tab to an egg and press Enter or Space to collect it.</p><div>{Array.from({length:EGG_COUNT},(_,id) => <button key={id} disabled={collected.includes(id)} onClick={() => collect(id)}><span style={{background:EGG_COLORS[id % EGG_COLORS.length]}} aria-hidden="true" />{collected.includes(id) ? '✓ In basket' : `Collect egg ${id+1}`}</button>)}</div></div>}
      <div className="meadow-signoff"><a href="#">egg</a><span>EVERYTHING YOU MEANT TO KEEP.</span><a href="#">BACK TO TOP ↑</a></div>
    </section>
  </div>;
}
