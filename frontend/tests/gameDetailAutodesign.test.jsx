import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import GameDetailView from '../src/components/GameDetailView.jsx';

function makePhoto(summaryOverrides = {}) {
  return {
    id: 'dream_whisperer_cat__cat',
    filename: 'dream_whisperer_cat__cat.png',
    label: 'Cat',
    src: '/activity-assets/dream_whisperer_cat__cat/entity_hero__round_512.png',
    summary: {
      category: 'category_1',
      template_type: 'cat1',
      source: 'autodesign',
      support_status: 'supported',
      support_level: 'full',
      asset_readiness: 'ready',
      entity_binding: { entity_id: 'cat', display_label: 'Cat' },
      plain_description: 'Imagine a sleeping cat dream.',
      steps_summary: ['Peek at the dream', 'Tell tiny scenes'],
      role_title: 'Dream Whisperer',
      ib_key_concept: 'Reflection',
      ...summaryOverrides,
    },
  };
}

describe('GameDetailView autodesign metadata', () => {
  it('shows entity binding, support status, and asset readiness for imported demos', () => {
    render(<GameDetailView photo={makePhoto()} onBack={vi.fn()} onStart={vi.fn()} isLoading={false} />);

    expect(screen.getByText('Imported')).toBeTruthy();
    expect(screen.getByText('Supported')).toBeTruthy();
    expect(screen.getByText('Assets ready')).toBeTruthy();
    expect(screen.getByText('cat')).toBeTruthy();
  });

  it('disables start when required assets are blocked', () => {
    render(
      <GameDetailView
        photo={makePhoto({
          asset_readiness: 'blocked',
          asset_readiness_detail: { required_missing: ['entity_hero'] },
        })}
        onBack={vi.fn()}
        onStart={vi.fn()}
        isLoading={false}
      />,
    );

    expect(screen.getByRole('button', { name: /Start unavailable/ }).disabled).toBe(true);
    expect(screen.getByText(/entity_hero/)).toBeTruthy();
  });

  it('disables start when partial readiness includes missing required assets', () => {
    render(
      <GameDetailView
        photo={makePhoto({
          asset_readiness: 'partial',
          asset_readiness_detail: { required_missing: ['collection_card'] },
        })}
        onBack={vi.fn()}
        onStart={vi.fn()}
        isLoading={false}
      />,
    );

    expect(screen.getByRole('button', { name: /Start unavailable/ }).disabled).toBe(true);
    expect(screen.getByText(/collection_card/)).toBeTruthy();
  });
});
