import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { cwd } from 'node:process';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import WonderLensDevice from '../src/activityGame/WonderLensDevice.jsx';

const CSS = readFileSync(join(cwd(), 'src/index.css'), 'utf8');

function cssBlock(selector) {
  const start = CSS.indexOf(`${selector} {`);
  const end = CSS.indexOf('\n}', start);
  return CSS.slice(start, end);
}

describe('WonderLensDevice', () => {
  it('renders preserved device controls and top-right scroll control', () => {
    render(
      <WonderLensDevice
        activity={{ name: 'Word Echo Practice', mechanic: 'remember' }}
        latestAiText="Repeat after me. Now try the long gentle echo again with your clearest voice so the device can keep showing the whole prompt."
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
    expect(screen.getByText('Pick')).toBeTruthy();
    expect(screen.getByText('Start')).toBeTruthy();
    expect(screen.getByAltText('Word Echo Practice visual')).toBeTruthy();
    expect(screen.queryByText(/Repeat after me/)).toBeNull();
  });

  it('keeps prototype side-control proportions in CSS', () => {
    expect(cssBlock('.wonderlens-device-shell')).toContain('width: min(calc(22rem * var(--wonderlens-device-scale, 1)), 88vw)');
    expect(cssBlock('.wonderlens-device')).toContain('aspect-ratio: 0.7 / 1');
    expect(cssBlock('.wonderlens-device__left-grip')).toContain('height: 43%');
    expect(cssBlock('.wonderlens-device__left-grip')).toContain('clip-path: polygon(0 0, 100% 2%, 92% 100%, 42% 100%)');
    expect(cssBlock('.wonderlens-device__scroll')).toContain('right: -8.8%');
    expect(cssBlock('.wonderlens-device__scroll')).toContain('width: 8.2%');
    expect(cssBlock('.wonderlens-device__scroll')).toContain('height: 14.3%');
    expect(cssBlock('.wonderlens-device__scroll')).toContain('border-radius: 0 999px 999px 0');
    expect(cssBlock('.wonderlens-device__control-label')).toContain('color: oklch(0.29 0.06 150)');
    expect(cssBlock('.wonderlens-device__primary-arrow')).toContain('border-color: oklch(0.28 0.07 150)');
    expect(cssBlock('.wonderlens-device__small-button')).toContain('right: 7.5%');
    expect(cssBlock('.wonderlens-device__primary')).toContain('bottom: 5.8%');
  });

  it('animates visual beat changes without making the asset interactive', () => {
    const { rerender } = render(
      <WonderLensDevice
        activity={{ name: 'Story Challenge Unlock', mechanic: 'imagine' }}
        latestAiText="The fox reaches the moon door."
        progress={{ current: 1, total: 3 }}
        assetSrc="/activity-assets/activity_story_challenge_unlock/round_1.png"
        savedTokens={[]}
        onScrollPrevious={vi.fn()}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    const firstImage = screen.getByAltText('Story Challenge Unlock visual');
    expect(firstImage.getAttribute('src')).toContain('round_1.png');

    rerender(
      <WonderLensDevice
        activity={{ name: 'Story Challenge Unlock', mechanic: 'imagine' }}
        latestAiText="The sleepy owl bridge waits."
        progress={{ current: 2, total: 3 }}
        assetSrc="/activity-assets/activity_story_challenge_unlock/round_2.png"
        savedTokens={[]}
        onScrollPrevious={vi.fn()}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    const nextImage = screen.getByAltText('Story Challenge Unlock visual');
    expect(nextImage.getAttribute('src')).toContain('round_2.png');
    expect(cssBlock('.activity-lens__media img')).toContain('animation: activity-lens-beat-in');
    expect(CSS).toContain('@keyframes activity-lens-beat-in');
    expect(screen.queryByRole('button', { name: /Story Challenge Unlock visual/i })).toBeNull();
  });

  it('renders metadata-driven screen layouts with visual-only choice assets', () => {
    render(
      <WonderLensDevice
        activity={{ name: 'Recognition Pop Challenge', mechanic: 'recognize' }}
        latestAiText="Find the animal."
        progress={{ current: 1, total: 3 }}
        assetSrc="/activity-assets/activity_recognition_pop_challenge/round_1.png"
        screenLayout={{
          mode: 'choice2',
          background: {
            src: '/activity-assets/activity_recognition_pop_challenge/round_1.png',
            fit: 'cover',
          },
          items: [
            {
              id: 'dog',
              src: '/activity-assets/activity_recognition_pop_challenge/round_1.png',
              shape: 'circle',
              label: 'Dog',
            },
            {
              id: 'cat',
              src: '/activity-assets/activity_recognition_pop_challenge/round_2.png',
              shape: 'rect3x4',
              label: 'Cat',
            },
          ],
        }}
        savedTokens={[]}
        onScrollPrevious={vi.fn()}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    expect(screen.getByAltText('Recognition Pop Challenge visual')).toBeTruthy();
    expect(screen.getByText('Dog')).toBeTruthy();
    expect(screen.getByText('Cat')).toBeTruthy();
    expect(cssBlock('.activity-screen-layout--choice2 .activity-screen-layout__items')).toContain('grid-template-columns: repeat(2, minmax(0, 1fr))');
    expect(cssBlock('.activity-screen-layout__item--circle')).toContain('border-radius: 50%');
    expect(cssBlock('.activity-screen-layout__item--rect3x4')).toContain('aspect-ratio: 3 / 4');
    expect(screen.queryByRole('button', { name: /Dog/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /Cat/i })).toBeNull();
  });

  it('renders picker layouts as a centered crown-style selector', () => {
    render(
      <WonderLensDevice
        activity={{ name: 'Phoneme Treasure Hunt', mechanic: 'collect' }}
        progress={{ current: 1, total: 3 }}
        assetSrc="/activity-assets/activity_phoneme_treasure_hunt/round_1.png"
        screenLayout={{
          mode: 'picker',
          background: {
            src: '/activity-assets/activity_phoneme_treasure_hunt/round_1.png',
            fit: 'cover',
          },
          items: [
            {
              id: 'ball',
              src: '/activity-assets/activity_phoneme_treasure_hunt/items/ball.png',
              shape: 'circle',
              label: 'Ball',
            },
            {
              id: 'basket',
              src: '/activity-assets/activity_phoneme_treasure_hunt/items/basket.png',
              shape: 'circle',
              label: 'Basket',
              selected: true,
            },
            {
              id: 'banana',
              src: '/activity-assets/activity_phoneme_treasure_hunt/items/banana.png',
              shape: 'circle',
              label: 'Banana',
            },
          ],
        }}
        onScrollPrevious={vi.fn()}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    expect(screen.getByText('Basket').closest('.activity-screen-layout__item')?.className).toContain('is-current');
    expect(cssBlock('.activity-screen-layout--picker .activity-screen-layout__items')).toContain('grid-template-rows');
    expect(cssBlock('.activity-screen-layout--picker .activity-screen-layout__item.is-current')).toContain('transform: scale(1)');
    expect(cssBlock('.activity-screen-layout--picker .activity-screen-layout__item.is-adjacent')).toContain('opacity');
  });

  it('can render Cat5 picker items without visible labels on transparent surfaces', () => {
    render(
      <WonderLensDevice
        activity={{ name: 'Phoneme Treasure Hunt', mechanic: 'collect' }}
        progress={{ current: 1, total: 3 }}
        screenLayout={{
          mode: 'picker',
          selection: 'device-scroll',
          hideLabels: true,
          transparentItems: true,
          background: { src: '/activity-assets/activity_phoneme_treasure_hunt/round_1.png', fit: 'cover' },
          items: [
            {
              id: 'ball',
              src: '/activity-assets/activity_phoneme_treasure_hunt/items/ball.png',
              shape: 'circle',
              label: 'Ball',
              selected: true,
            },
          ],
        }}
        onScrollPrevious={vi.fn()}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    expect(screen.queryByText('Ball')).toBeNull();
    expect(document.querySelector('.activity-screen-layout--transparent-items')).toBeTruthy();
    expect(document.querySelectorAll('.activity-screen-layout__item span')).toHaveLength(0);
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item')).toContain('background: transparent');
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item')).toContain('overflow: hidden');
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item')).toContain('border-color: transparent');
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item.is-selected')).toContain('background: transparent');
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item.is-selected')).not.toContain('0 0 0 0.12rem');
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item.is-selected')).toContain('box-shadow: none');
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item img')).toContain('width: 92%');
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item img')).toContain('height: 92%');
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item img')).toContain('object-fit: contain');
    expect(cssBlock('.activity-screen-layout--transparent-items .activity-screen-layout__item img')).toContain('border-radius: inherit');
  });

  it('keeps Cat3 Done Help inside the lens as a curved side rail', () => {
    render(
      <WonderLensDevice
        activity={{ name: 'Guided Drawing', mechanic: 'build' }}
        progress={{ current: 1, total: 3 }}
        assetSrc="/activity-assets/activity_guided_drawing/round_1.png"
        optionRail={{
          label: 'Build response options',
          selectedIndex: 1,
          options: [
            { label: 'Done', value: 'done' },
            { label: 'Help', value: 'help' },
          ],
        }}
        onScrollPrevious={vi.fn()}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    const panel = screen.getByRole('listbox', { name: 'Build response options' });
    expect(panel.className).toContain('activity-lens__option-rail');
    expect(screen.getByRole('option', { name: 'Done' })).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Help' }).getAttribute('aria-selected')).toBe('true');
    expect(document.querySelector('.wonderlens-device__option-rail')).toBeNull();
    expect(cssBlock('.activity-lens__option-rail')).toContain('right: 6%');
    expect(cssBlock('.activity-lens__option-rail')).toContain('top: 50%');
    expect(cssBlock('.activity-lens__option-rail')).toContain('transform: translateY(-50%)');
    expect(cssBlock('.activity-lens__option-rail')).toContain('grid-template-rows: repeat(2, minmax(0, 1fr))');
    expect(cssBlock('.activity-lens__option-rail')).toContain('background: oklch(0.98 0.012 145 / 0.18)');
    expect(cssBlock('.activity-lens__option.is-selected')).toContain('transform: scale(1.16)');
  });

  it('shows an in-lens waiting state while the backend is responding', () => {
    render(
      <WonderLensDevice
        activity={{ name: 'Career Decision Role Play', mechanic: 'decide' }}
        latestAiText="Which firefighter tool should we use first?"
        progress={{ current: 1, total: 3 }}
        assetSrc="/activity-assets/activity_career_decision_role_play/round_1.png"
        savedTokens={[]}
        isWaiting
        onScrollPrevious={vi.fn()}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    expect(screen.getByRole('status', { name: 'WonderLens is thinking' })).toBeTruthy();
    expect(cssBlock('.activity-lens__waiting')).toContain('animation: activity-lens-waiting-pulse');
    expect(CSS).toContain('@keyframes activity-lens-waiting-pulse');
  });
});
