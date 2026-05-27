import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import ActivityTranscript from '../src/activityGame/ActivityTranscript.jsx';

describe('ActivityTranscript', () => {
  it('renders AI and child profile images for transcript messages', () => {
    render(
      <ActivityTranscript
        messages={[
          { role: 'ai', text: 'Ready for the echo?' },
          { role: 'child', text: 'Ready' },
        ]}
        loading={false}
        turnPending={false}
      />,
    );

    expect(screen.getByLabelText('WonderLens profile')).toBeTruthy();
    expect(screen.getByLabelText('Child profile')).toBeTruthy();
  });

  it('shows a waiting indicator while the backend turn is pending', () => {
    render(<ActivityTranscript messages={[]} loading={false} turnPending />);

    expect(screen.getByRole('status')).toBeTruthy();
    expect(screen.getByLabelText('WonderLens is thinking')).toBeTruthy();
  });
});
