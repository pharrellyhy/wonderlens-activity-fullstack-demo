import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import WonderLensDevice from '../src/activityGame/WonderLensDevice.jsx';

describe('WonderLensDevice', () => {
  it('renders preserved device controls and top-right scroll control', () => {
    render(
      <WonderLensDevice
        activity={{ name: 'Word Echo Practice', mechanic: 'remember' }}
        latestAiText="Repeat after me."
        progress={{ current: 1, total: 3 }}
        assetSrc="/activity-assets/activity_word_echo_practice/intro.png"
        savedTokens={['ready']}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    expect(screen.getByTestId('wonderlens-device')).toBeTruthy();
    expect(screen.getByLabelText('Scroll activity lens')).toBeTruthy();
    expect(screen.getByLabelText('Start or restart activity')).toBeTruthy();
    expect(screen.getByText('Word Echo Practice')).toBeTruthy();
    expect(screen.getByText('Repeat after me.')).toBeTruthy();
    expect(screen.getByAltText('Word Echo Practice visual')).toBeTruthy();
  });
});
