import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { render } from './utils';
import { FamiliesPage } from '../pages/FamiliesPage';

// Mock the familyService
vi.mock('../services/familyService', () => ({
  familyService: {
    getFamilies: vi.fn(() => Promise.resolve({ data: [] })),
  },
}));

describe('FamiliesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders families page with header', async () => {
    render(<FamiliesPage />);
    
    await waitFor(() => {
      expect(screen.getAllByText(/family groups/i)).toHaveLength(2);
    });
  });

  it('displays empty state when no families exist', async () => {
    render(<FamiliesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/no families yet/i)).toBeInTheDocument();
    });
  });
});
