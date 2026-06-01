import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { cwd } from 'node:process';
import { describe, expect, it } from 'vitest';

const css = readFileSync(join(cwd(), 'src', 'index.css'), 'utf8');

describe('activity game short viewport layout CSS', () => {
  it('uses CSS variables so the activity game grid can be resized', () => {
    const gameStart = css.indexOf('.activity-game {');
    const nextRuleStart = css.indexOf('.activity-game__topbar', gameStart);
    const gameBlock = css.slice(gameStart, nextRuleStart);

    expect(gameBlock).toContain('--activity-game-size');
    expect(gameBlock).toContain('--activity-game-stage-min');
    expect(gameBlock).toMatch(/width:\s*min\(calc\(61rem \* var\(--activity-game-size\)/);
    expect(gameBlock).toMatch(/height:\s*min\(calc\(64rem \* var\(--activity-game-size\)/);
    expect(gameBlock).toContain('grid-template-rows: var(--activity-game-topbar-row)');
  });

  it('caps the picker stage in short viewports so the intro transcript stays in the first view', () => {
    const mediaStart = css.indexOf('@media (max-height: 980px)');
    const nextMediaStart = css.indexOf('@media', mediaStart + 1);
    const shortViewportBlock = css.slice(mediaStart, nextMediaStart === -1 ? css.length : nextMediaStart);

    expect(shortViewportBlock).toContain('.activity-game__stage');
    expect(shortViewportBlock).toMatch(/\.activity-game__stage\s*\{[\s\S]*max-height:/);
    expect(shortViewportBlock).toMatch(/\.activity-game__stage\s*\{[\s\S]*overflow:\s*hidden/);
    expect(shortViewportBlock).toContain('grid-template-rows: clamp(4.2rem');
    expect(shortViewportBlock).toMatch(/\.activity-game__list\s*\{[\s\S]*overflow:\s*auto/);
    expect(shortViewportBlock).toMatch(/\.activity-game__transcript\s*\{[\s\S]*overflow:\s*hidden/);
    expect(shortViewportBlock).toMatch(/\.activity-transcript__messages\s*\{[\s\S]*min-height:\s*0/);
  });
});
