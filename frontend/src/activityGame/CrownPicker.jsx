import { useCallback, useEffect, useRef } from 'react';

const PICKER_ID = 'crown-picker';
const DETENT_THRESHOLD = 80;
const MOMENTUM_DECAY = 0.82;
const MOMENTUM_MIN = 8;

function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

function offsetClass(index, focusedIndex) {
  const delta = index - focusedIndex;
  if (delta === 0) return 'is-current';
  if (delta === -1) return 'is-adjacent is-previous';
  if (delta === 1) return 'is-adjacent is-next';
  return 'is-far';
}

export default function CrownPicker({
  items = [],
  index = 0,
  onStep,
  onConfirm,
  disabled = false,
  label = 'Crown picker',
  confirmLabel = 'Select',
}) {
  const total = items.length;
  const focusedIndex = total ? Math.max(0, Math.min(index, total - 1)) : 0;
  const velocityRef = useRef(0);
  const accumulatorRef = useRef(0);
  const frameRef = useRef(0);
  const settleRef = useRef(null);
  const onStepRef = useRef(onStep);

  const stopMomentum = useCallback(() => {
    if (frameRef.current) {
      window.cancelAnimationFrame(frameRef.current);
      frameRef.current = 0;
    }
    velocityRef.current = 0;
    accumulatorRef.current = 0;
  }, []);

  const drainDetents = useCallback(() => {
    while (Math.abs(accumulatorRef.current) >= DETENT_THRESHOLD) {
      const direction = accumulatorRef.current > 0 ? 1 : -1;
      accumulatorRef.current -= direction * DETENT_THRESHOLD;
      onStepRef.current?.(direction);
    }
  }, []);

  const settle = useCallback(() => {
    velocityRef.current *= MOMENTUM_DECAY;
    accumulatorRef.current += velocityRef.current;
    drainDetents();
    if (Math.abs(velocityRef.current) > MOMENTUM_MIN) {
      frameRef.current = window.requestAnimationFrame(settleRef.current);
    } else {
      accumulatorRef.current = 0;
      velocityRef.current = 0;
      frameRef.current = 0;
    }
  }, [drainDetents]);

  const handleWheel = useCallback((event) => {
    if (disabled || total <= 1) return;
    accumulatorRef.current += event.deltaY;
    drainDetents();
    if (prefersReducedMotion()) {
      accumulatorRef.current = 0;
      return;
    }
    velocityRef.current = event.deltaY;
    if (!frameRef.current) {
      frameRef.current = window.requestAnimationFrame(settleRef.current);
    }
  }, [disabled, drainDetents, total]);

  const step = useCallback((direction) => {
    if (disabled || total <= 1) return;
    stopMomentum();
    onStepRef.current?.(direction);
  }, [disabled, stopMomentum, total]);

  const handleKeyDown = useCallback((event) => {
    if (disabled) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      step(1);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      step(-1);
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (total) onConfirm?.(focusedIndex);
    }
  }, [disabled, focusedIndex, onConfirm, step, total]);

  useEffect(() => {
    onStepRef.current = onStep;
    settleRef.current = settle;
  });

  useEffect(() => stopMomentum, [stopMomentum]);

  return (
    <div className="crown-picker" data-testid="crown-picker" onWheel={handleWheel}>
      <ul
        className="crown-picker__list"
        role="listbox"
        aria-label={label}
        aria-disabled={disabled ? 'true' : 'false'}
        aria-activedescendant={total ? `${PICKER_ID}-option-${focusedIndex}` : undefined}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
      >
        {items.map((item, itemIndex) => (
          <li
            key={item.id || itemIndex}
            id={`${PICKER_ID}-option-${itemIndex}`}
            className={`crown-picker__option ${offsetClass(itemIndex, focusedIndex)}`}
            role="option"
            aria-selected={itemIndex === focusedIndex ? 'true' : 'false'}
            aria-label={item.label || item.id || undefined}
          >
            {item.image || item.src ? (
              <img className="crown-picker__option-image" src={item.image || item.src} alt="" aria-hidden="true" />
            ) : (
              <span className="crown-picker__option-label">{item.label || item.id || ''}</span>
            )}
          </li>
        ))}
      </ul>

      <span className="crown-picker__arc" aria-hidden="true" />

      <div className="crown-picker__controls">
        <button
          type="button"
          className="crown-picker__step crown-picker__step--up"
          aria-label="Previous item"
          disabled={disabled || total <= 1}
          onClick={() => step(-1)}
        />
        <button
          type="button"
          className="crown-picker__step crown-picker__step--down"
          aria-label="Next item"
          disabled={disabled || total <= 1}
          onClick={() => step(1)}
        />
        <button
          type="button"
          className="crown-picker__confirm"
          aria-label={confirmLabel}
          disabled={disabled || !total}
          onClick={() => onConfirm?.(focusedIndex)}
        >
          <span className="crown-picker__confirm-arrow" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
