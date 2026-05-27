import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import WonderLensDevice from '../src/activityGame/WonderLensDevice.jsx';

function cssBlock(selector) {
  const css = readFileSync(join(process.cwd(), 'src/index.css'), 'utf8');
  const start = css.indexOf(`${selector} {`);
  const end = css.indexOf('\n}', start);
  return css.slice(start, end);
}

describe('WonderLensDevice', () => {
  it('renders preserved device controls and top-right scroll control', () => {
    render(
      <WonderLensDevice
        activity={{ name: 'Word Echo Practice', mechanic: 'remember' }}
        latestAiText="Repeat after me."
        progress={{ current: 1, total: 3 }}
        assetSrc="/activity-assets/activity_word_echo_practice/intro.png"
        savedTokens={['ready']}
        onScrollPrevious={vi.fn()}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    expect(screen.getByTestId('wonderlens-device')).toBeTruthy();
    expect(screen.getByLabelText('Scroll activity lens')).toBeTruthy();
    expect(screen.getByLabelText('Previous activity')).toBeTruthy();
    expect(screen.getByLabelText('Next activity')).toBeTruthy();
    expect(screen.getByLabelText('Start or restart activity')).toBeTruthy();
    expect(screen.getByText('Word Echo Practice')).toBeTruthy();
    expect(screen.getByText('Repeat after me.')).toBeTruthy();
    expect(screen.getByAltText('Word Echo Practice visual')).toBeTruthy();
  });

  it('keeps prototype side-control proportions in CSS', () => {
    expect(cssBlock('.wonderlens-device')).toContain('aspect-ratio: 0.7 / 1');
    expect(cssBlock('.wonderlens-device__left-grip')).toContain('height: 43%');
    expect(cssBlock('.wonderlens-device__left-grip')).toContain('clip-path: polygon(0 0, 100% 2%, 92% 100%, 42% 100%)');
    expect(cssBlock('.wonderlens-device__scroll')).toContain('right: -8.8%');
    expect(cssBlock('.wonderlens-device__scroll')).toContain('width: 8.2%');
    expect(cssBlock('.wonderlens-device__scroll')).toContain('height: 14.3%');
    expect(cssBlock('.wonderlens-device__scroll')).toContain('border-radius: 0 999px 999px 0');
    expect(cssBlock('.activity-lens__text')).toContain('background: oklch(0.16 0.018 155 / 0.82)');
    expect(cssBlock('.wonderlens-device__small-button')).toContain('right: 7.5%');
    expect(cssBlock('.wonderlens-device__primary')).toContain('bottom: 5.8%');
  });
});
