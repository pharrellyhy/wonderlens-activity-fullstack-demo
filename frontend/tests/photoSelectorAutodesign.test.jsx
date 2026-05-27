import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import PhotoSelector from '../src/components/PhotoSelector.jsx';

const importedCategoryPayload = {
  categories: [
    {
      id: 'cat1',
      title: 'In-Device Verbal',
      subtitle: 'Imagine stories with your photo friend!',
      photos: [
        {
          id: 'dream_whisperer_cat__cat',
          activity_type: 'dream_whisperer_cat__cat',
          filename: 'dream_whisperer_cat__cat.png',
          entity_id: 'cat',
          label: 'Cat',
          src: '/activity-assets/dream_whisperer_cat__cat/entity_hero__round_512.png',
          summary: {
            category: 'category_1',
            template_type: 'cat1',
            source: 'autodesign',
            support_status: 'supported',
            asset_readiness: 'ready',
            entity_binding: { entity_id: 'cat', display_label: 'Cat' },
            plain_description: 'Imagine a sleeping cat dream.',
            steps_summary: ['Peek at the dream', 'Tell tiny scenes'],
            role_title: 'Dream Whisperer',
          },
        },
        {
          id: 'blocked_fixture__leaf',
          activity_type: 'blocked_fixture__leaf',
          filename: 'blocked_fixture__leaf.png',
          entity_id: 'leaf',
          label: 'Leaf',
          src: '/activity-assets/blocked_fixture__leaf/entity_hero__round_512.png',
          summary: {
            category: 'category_1',
            template_type: 'cat1',
            source: 'autodesign',
            support_status: 'supported',
            asset_readiness: 'blocked',
            asset_readiness_detail: { required_missing: ['entity_hero'] },
            entity_binding: { entity_id: 'leaf', display_label: 'Leaf' },
            plain_description: 'Blocked asset fixture.',
            steps_summary: ['Needs a real hero asset'],
            role_title: 'Leaf Looker',
          },
        },
      ],
    },
    {
      id: 'cat5',
      title: 'Out-of-Device Collection',
      subtitle: 'Go on a real-world scavenger hunt!',
      photos: [
        {
          id: 'concept_phoneme_hunt_collect__ball',
          activity_type: 'concept_phoneme_hunt_collect__ball',
          filename: 'concept_phoneme_hunt_collect__ball.png',
          entity_id: 'ball',
          label: 'Ball',
          src: '/activity-assets/concept_phoneme_hunt_collect__ball/ball_sound_card__icon_256.png',
          summary: {
            category: 'category_5',
            template_type: 'cat5',
            source: 'autodesign',
            support_status: 'degraded',
            degraded_reasons: ['Reference-bound asset is reviewer-only.'],
            asset_readiness: 'partial',
            entity_binding: { entity_id: 'ball', display_label: 'Ball' },
            plain_description: 'Find things that start with b.',
            steps_summary: ['Find a b sound', 'Collect matches'],
            role_title: 'B-Sound Scout',
            collection_count: 2,
            collectible_previews: [],
          },
        },
      ],
    },
  ],
};

function mockFetch() {
  return vi.fn((url) => {
    if (String(url).includes('/api/entities')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(importedCategoryPayload),
      });
    }
    return Promise.resolve({
      ok: true,
      blob: () => Promise.resolve(new Blob(['image'], { type: 'image/png' })),
    });
  });
}

describe('PhotoSelector autodesign activities', () => {
  beforeEach(() => {
    globalThis.fetch = mockFetch();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows supported imports by default and gates degraded imports behind an explicit toggle', async () => {
    render(<PhotoSelector onPhotoSelect={vi.fn()} isLoading={false} />);

    expect((await screen.findAllByText('Imported')).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /Cat Cat Imported/ })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Ball/ })).toBeNull();

    fireEvent.click(screen.getByRole('checkbox', { name: /Include degraded/ }));

    expect(await screen.findByRole('button', { name: /Ball Ball Degraded partial/ })).toBeTruthy();
    expect(screen.getAllByText('Degraded').length).toBeGreaterThan(1);
  });

  it('starts imported demos with the backend-provided filename', async () => {
    const onPhotoSelect = vi.fn();
    render(<PhotoSelector onPhotoSelect={onPhotoSelect} isLoading={false} />);

    expect((await screen.findAllByText('Imported')).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: /Cat Cat Imported/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Start Adventure/ }));

    await waitFor(() => expect(onPhotoSelect).toHaveBeenCalledTimes(1));
    expect(onPhotoSelect.mock.calls[0][0].name).toBe('dream_whisperer_cat__cat.png');
  });

  it('lets blocked imports open details so missing asset reasons are visible', async () => {
    render(<PhotoSelector onPhotoSelect={vi.fn()} isLoading={false} />);

    const blockedCard = await screen.findByRole('button', { name: /Leaf Leaf Imported blocked/ });
    fireEvent.click(blockedCard);

    expect(await screen.findByText(/Missing required: entity_hero/)).toBeTruthy();
    expect(screen.getByRole('button', { name: /Start unavailable/ }).disabled).toBe(true);
  });
});
