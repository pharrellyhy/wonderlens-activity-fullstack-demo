import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent, screen } from '@testing-library/react';
import FeedbackQuickFlag from '../src/components/feedback/FeedbackQuickFlag.jsx';

describe('FeedbackQuickFlag', () => {
  it('renders the header with the current turn number', () => {
    render(
      <FeedbackQuickFlag
        turnNumber={3}
        screenshotBlob={null}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByText('Flag turn 3')).toBeTruthy();
  });

  it('disables Save by default and enables it after selecting a tag', () => {
    render(
      <FeedbackQuickFlag
        turnNumber={3}
        screenshotBlob={null}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    const saveButton = screen.getByRole('button', { name: 'Save' });
    expect(saveButton.disabled).toBe(true);

    fireEvent.click(screen.getByRole('button', { name: 'Tone' }));
    expect(saveButton.disabled).toBe(false);
  });

  it('calls onSave with selected tags and empty note when Save is clicked', () => {
    const onSave = vi.fn();
    render(
      <FeedbackQuickFlag
        turnNumber={3}
        screenshotBlob={null}
        onSave={onSave}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Tone' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledWith({ tags: ['tone'], quickNote: '' });
  });

  it('calls onCancel when Cancel is clicked', () => {
    const onCancel = vi.fn();
    render(
      <FeedbackQuickFlag
        turnNumber={3}
        screenshotBlob={null}
        onSave={vi.fn()}
        onCancel={onCancel}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('prefills tags + note and shows the edit header when isEditing is true', () => {
    const onSave = vi.fn();
    render(
      <FeedbackQuickFlag
        turnNumber={5}
        screenshotBlob={null}
        initialTags={['tone', 'confusing']}
        initialQuickNote='too preachy'
        isEditing
        onSave={onSave}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByText('Edit flag for turn 5')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Tone', pressed: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Confusing', pressed: true })).toBeTruthy();
    const note = screen.getByPlaceholderText('Short note (optional)');
    expect(note.value).toBe('too preachy');

    // Save with the prefilled values intact
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(onSave).toHaveBeenCalledWith({ tags: ['tone', 'confusing'], quickNote: 'too preachy' });
  });
});
