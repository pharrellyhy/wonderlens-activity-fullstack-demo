import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { cwd } from 'node:process';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import CrownPicker from '../src/activityGame/CrownPicker.jsx';

const CSS = readFileSync(join(cwd(), 'src/index.css'), 'utf8');

function cssBlock(selector) {
  const start = CSS.indexOf(`${selector} {`);
  const end = CSS.indexOf('\n}', start);
  return CSS.slice(start, end);
}

const ITEMS = [
  { id: 'ball', label: 'Ball' },
  { id: 'basket', label: 'Basket' },
  { id: 'banana', label: 'Banana' },
];

describe('CrownPicker vertical-list layout', () => {
  it('renders a listbox with one option per item and marks the focused row', () => {
    render(<CrownPicker items={ITEMS} index={1} onStep={vi.fn()} onConfirm={vi.fn()} />);

    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });
    expect(listbox).toBeTruthy();
    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(3);
    expect(screen.getByRole('option', { name: 'Basket' }).getAttribute('aria-selected')).toBe('true');
    expect(screen.getByRole('option', { name: 'Ball' }).getAttribute('aria-selected')).toBe('false');
    expect(listbox.getAttribute('aria-activedescendant')).toBe('crown-picker-option-1');
  });

  it('classes the focused item as current and neighbors as adjacent rings', () => {
    render(<CrownPicker items={ITEMS} index={1} onStep={vi.fn()} onConfirm={vi.fn()} />);

    expect(screen.getByRole('option', { name: 'Basket' }).className).toContain('is-current');
    expect(screen.getByRole('option', { name: 'Ball' }).className).toContain('is-previous');
    expect(screen.getByRole('option', { name: 'Banana' }).className).toContain('is-next');
  });

  it('renders the arc scroll indicator and a green confirm control', () => {
    render(<CrownPicker items={ITEMS} index={0} onStep={vi.fn()} onConfirm={vi.fn()} />);

    expect(document.querySelector('.crown-picker__arc')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Select' })).toBeTruthy();
  });

  it('keeps the focused row centered/enlarged and neighbors scaled and faded in CSS', () => {
    expect(cssBlock('.crown-picker__option.is-current')).toContain('transform: scale(1)');
    expect(cssBlock('.crown-picker__option.is-current')).toContain('opacity: 1');
    expect(cssBlock('.crown-picker__option.is-previous')).toContain('scale(0.72)');
    expect(cssBlock('.crown-picker__option.is-next')).toContain('scale(0.72)');
    expect(cssBlock('.crown-picker__option.is-far')).toContain('scale(0.5)');
    expect(cssBlock('.crown-picker__option.is-adjacent')).toContain('opacity');
  });
});

describe('CrownPicker crown interaction', () => {
  it('steps focus by one detent per click via onStep', () => {
    const onStep = vi.fn();
    render(<CrownPicker items={ITEMS} index={1} onStep={onStep} onConfirm={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Next item' }));
    expect(onStep).toHaveBeenLastCalledWith(1);

    fireEvent.click(screen.getByRole('button', { name: 'Previous item' }));
    expect(onStep).toHaveBeenLastCalledWith(-1);
  });

  it('settles momentum onto the nearest detent with one onStep per click', () => {
    vi.useFakeTimers();
    let rafId = 0;
    const callbacks = new Map();
    vi.stubGlobal('requestAnimationFrame', (cb) => {
      rafId += 1;
      callbacks.set(rafId, cb);
      return rafId;
    });
    vi.stubGlobal('cancelAnimationFrame', (id) => callbacks.delete(id));

    const onStep = vi.fn();
    render(<CrownPicker items={ITEMS} index={0} onStep={onStep} onConfirm={vi.fn()} />);

    const down = screen.getByRole('button', { name: 'Next item' });
    fireEvent.wheel(down, { deltaY: 240 });
    // Drain queued animation frames to let momentum decay and settle.
    for (let frame = 0; frame < 30 && callbacks.size; frame += 1) {
      const [[id, cb]] = callbacks;
      callbacks.delete(id);
      cb(performance.now());
    }

    expect(onStep).toHaveBeenCalled();
    onStep.mock.calls.forEach(([delta]) => {
      expect([1, -1]).toContain(delta);
    });

    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('does not fire onStep while disabled', () => {
    const onStep = vi.fn();
    render(<CrownPicker items={ITEMS} index={1} onStep={onStep} onConfirm={vi.fn()} disabled />);

    expect(screen.getByRole('button', { name: 'Next item' }).disabled).toBe(true);
    fireEvent.wheel(screen.getByTestId('crown-picker'), { deltaY: 240 });
    expect(onStep).not.toHaveBeenCalled();
  });
});

describe('CrownPicker confirm, keyboard, and accessibility', () => {
  it('fires onConfirm with the focused index when the green control is pressed', () => {
    const onConfirm = vi.fn();
    render(<CrownPicker items={ITEMS} index={2} onStep={vi.fn()} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByRole('button', { name: 'Select' }));
    expect(onConfirm).toHaveBeenCalledWith(2);
  });

  it('maps ArrowDown/ArrowUp to step and Enter to confirm', () => {
    const onStep = vi.fn();
    const onConfirm = vi.fn();
    render(<CrownPicker items={ITEMS} index={1} onStep={onStep} onConfirm={onConfirm} />);

    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });
    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    expect(onStep).toHaveBeenLastCalledWith(1);
    fireEvent.keyDown(listbox, { key: 'ArrowUp' });
    expect(onStep).toHaveBeenLastCalledWith(-1);
    fireEvent.keyDown(listbox, { key: 'Enter' });
    expect(onConfirm).toHaveBeenCalledWith(1);
  });

  it('exposes a keyboard-focusable listbox and ignores keys while disabled', () => {
    const onStep = vi.fn();
    const onConfirm = vi.fn();
    render(<CrownPicker items={ITEMS} index={1} onStep={onStep} onConfirm={onConfirm} disabled />);

    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });
    expect(listbox.getAttribute('tabindex')).toBe('-1');
    expect(screen.getByRole('button', { name: 'Select' }).disabled).toBe(true);
    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    fireEvent.keyDown(listbox, { key: 'Enter' });
    expect(onStep).not.toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('steps synchronously without momentum when reduced motion is preferred', () => {
    const matchMediaSpy = vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
    vi.stubGlobal('matchMedia', matchMediaSpy);
    const rafSpy = vi.fn();
    vi.stubGlobal('requestAnimationFrame', rafSpy);

    const onStep = vi.fn();
    render(<CrownPicker items={ITEMS} index={0} onStep={onStep} onConfirm={vi.fn()} />);

    fireEvent.wheel(screen.getByTestId('crown-picker'), { deltaY: 160 });
    expect(onStep).toHaveBeenCalledTimes(2);
    expect(rafSpy).not.toHaveBeenCalled();

    vi.unstubAllGlobals();
  });
});
