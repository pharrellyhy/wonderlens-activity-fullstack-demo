import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { cwd } from 'node:process';
import { describe, expect, it } from 'vitest';

const css = readFileSync(join(cwd(), 'src', 'index.css'), 'utf8');

describe('activity game short viewport layout CSS', () => {
  it('caps the picker stage in short viewports so the intro transcript stays in the first view', () => {
    const mediaStart = css.indexOf('@media (max-height: 980px)');
    const nextMediaStart = css.indexOf('@media', mediaStart + 1);
    const shortViewportBlock = css.slice(mediaStart, nextMediaStart === -1 ? css.length : nextMediaStart);

    expect(shortViewportBlock).toContain('.activity-game__stage');
    expect(shortViewportBlock).toMatch(/\.activity-game__stage\s*\{[\s\S]*max-height:/);
    expect(shortViewportBlock).toMatch(/\.activity-game__stage\s*\{[\s\S]*overflow:\s*hidden/);
    expect(shortViewportBlock).toMatch(/\.activity-game__list\s*\{[\s\S]*overflow:\s*auto/);
  });
});
