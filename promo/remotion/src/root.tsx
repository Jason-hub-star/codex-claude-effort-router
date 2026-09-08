import React from 'react';
import {AbsoluteFill, Composition, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

const colors = {
  ink: '#101828',
  muted: '#667085',
  paper: '#F8FAFC',
  cyan: '#06B6D4',
  green: '#10B981',
  amber: '#F59E0B',
  rose: '#F43F5E',
  violet: '#7C3AED',
};

const fade = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, start + 12, end - 12, end], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.cubic),
  });

const Center: React.FC<React.PropsWithChildren<{opacity?: number}>> = ({children, opacity = 1}) => (
  <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity}}>{children}</AbsoluteFill>
);

const Lane: React.FC<{name: string; detail: string; color: string; delay: number}> = ({name, detail, color, delay}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const scale = spring({frame: frame - delay, fps, config: {damping: 15, stiffness: 130}});
  return (
    <div style={{width: 238, padding: '24px 20px', borderRadius: 22, background: '#FFFFFF', border: `3px solid ${color}`, transform: `scale(${scale})`, boxShadow: '0 18px 40px rgba(16,24,40,.10)'}}>
      <div style={{fontSize: 27, fontWeight: 900, color}}>{name}</div>
      <div style={{fontSize: 17, color: colors.muted, marginTop: 9, lineHeight: 1.35}}>{detail}</div>
    </div>
  );
};

const Video: React.FC = () => {
  const frame = useCurrentFrame();
  const scene1 = fade(frame, 0, 105);
  const scene2 = fade(frame, 85, 235);
  const scene3 = fade(frame, 215, 350);
  const scene4 = fade(frame, 330, 450);
  const pulse = 1 + Math.sin(frame / 8) * 0.025;

  return (
    <AbsoluteFill style={{backgroundColor: colors.paper, color: colors.ink, fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif', overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: -180, background: 'radial-gradient(circle at 20% 20%, rgba(6,182,212,.12), transparent 32%), radial-gradient(circle at 80% 70%, rgba(124,58,237,.11), transparent 34%)'}} />

      <Center opacity={scene1}>
        <div style={{fontSize: 26, color: colors.rose, fontWeight: 800, letterSpacing: 2}}>ONE SETTING FOR EVERY TASK?</div>
        <div style={{fontSize: 72, fontWeight: 950, marginTop: 18, letterSpacing: -3}}>That gets expensive. Fast.</div>
        <div style={{fontSize: 27, color: colors.muted, marginTop: 22}}>Tiny lookup ≠ production migration</div>
      </Center>

      <Center opacity={scene2}>
        <div style={{position: 'absolute', top: 90, fontSize: 45, fontWeight: 950}}>Route effort by task risk</div>
        <div style={{display: 'flex', gap: 20, marginTop: 55}}>
          <Lane name="FAST" detail="exact + mechanical" color={colors.cyan} delay={95} />
          <Lane name="DAILY" detail="read + explain" color={colors.green} delay={102} />
          <Lane name="DEEP" detail="build + integrate" color={colors.amber} delay={109} />
          <Lane name="CRITICAL" detail="safety + security" color={colors.rose} delay={116} />
        </div>
      </Center>

      <Center opacity={scene3}>
        <div style={{fontSize: 27, color: colors.violet, fontWeight: 900, letterSpacing: 2}}>ONE DETERMINISTIC CLASSIFIER</div>
        <div style={{display: 'flex', alignItems: 'center', gap: 54, marginTop: 36}}>
          <div style={{padding: '30px 38px', borderRadius: 24, background: '#fff', border: `3px solid ${colors.green}`, fontSize: 35, fontWeight: 900, transform: `scale(${pulse})`}}>Prompt → Lane</div>
          <div style={{fontSize: 58, color: colors.muted}}>→</div>
          <div style={{display: 'grid', gap: 18}}>
            <div style={{padding: '20px 34px', borderRadius: 18, background: '#E6FAFD', border: `2px solid ${colors.cyan}`, fontSize: 29, fontWeight: 850}}>Codex profiles + agents</div>
            <div style={{padding: '20px 34px', borderRadius: 18, background: '#F0EAFE', border: `2px solid ${colors.violet}`, fontSize: 29, fontWeight: 850}}>Claude Code subagents</div>
          </div>
        </div>
        <div style={{fontSize: 22, color: colors.muted, marginTop: 34}}>Transparent: the active parent model never secretly changes.</div>
      </Center>

      <Center opacity={scene4}>
        <div style={{display: 'flex', gap: 18, marginBottom: 38}}>
          {['47 routing cases', 'fail-open', 'idempotent install'].map((item, i) => (
            <div key={item} style={{padding: '15px 23px', borderRadius: 999, color: '#fff', background: [colors.cyan, colors.rose, colors.green][i], fontSize: 20, fontWeight: 850}}>{item}</div>
          ))}
        </div>
        <div style={{fontSize: 66, fontWeight: 950, letterSpacing: -2}}>effort-lanes</div>
        <div style={{fontSize: 30, color: colors.violet, marginTop: 22, fontWeight: 850}}>Open source · MIT · tested evidence included</div>
        <div style={{fontSize: 24, color: colors.muted, marginTop: 30}}>github.com/Jason-hub-star</div>
      </Center>
    </AbsoluteFill>
  );
};

export const Root: React.FC = () => (
  <Composition id="EffortRouter" component={Video} durationInFrames={450} fps={30} width={1280} height={720} />
);
