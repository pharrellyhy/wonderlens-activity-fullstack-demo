import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PrototypeDeviceFrame from '../src/components/PrototypeDeviceFrame.jsx';
import RoundDevicePreview from '../src/components/RoundDevicePreview.jsx';

describe('Prototype device preview', () => {
  it('renders a circular child-facing screen without debug transcript content', () => {
    render(
      <PrototypeDeviceFrame>
        <RoundDevicePreview
          screenFrame={{
            widget: 'photo_display',
            widget_label: 'Dream scene',
            widget_params: { description: 'Cat dream cloud' },
          }}
          photoUrl="/activity-assets/dream_whisperer_cat__cat/entity_hero__round_512.png"
          sessionState={{ current_step: 'STEP_3_ROUND_1', current_round: 1, total_rounds: 3 }}
        />
      </PrototypeDeviceFrame>,
    );

    expect(screen.getByLabelText('Prototype round device preview')).toBeTruthy();
    expect(screen.getByText('Dream scene')).toBeTruthy();
    expect(screen.queryByText(/conversation_history/)).toBeNull();
    expect(screen.queryByText(/debug/i)).toBeNull();
  });

  it('applies compact frame and clamped title classes for constrained Cat5 layouts', () => {
    render(
      <PrototypeDeviceFrame compact>
        <RoundDevicePreview
          screenFrame={{
            widget: 'progress_tracker',
            widget_label: 'A very long imported activity label that must not overtake the round screen',
            widget_params: { description: 'Find a soft thing near the dandelion' },
          }}
          photoUrl="/activity-assets/fluffy_expedition_dandelion__dandelion/fuzzy_moss__round_512.png"
          sessionState={{ current_step: 'STEP_3_COLLECT_1', current_round: 1, total_rounds: 3 }}
        />
      </PrototypeDeviceFrame>,
    );

    expect(screen.getByLabelText('Prototype round device preview').className).toContain('prototype-device--compact');
    expect(screen.getByText(/very long imported activity label/).className).toContain('round-device-preview__title');
  });
});
