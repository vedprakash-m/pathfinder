import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../tests/utils';
import { HomePage } from '../pages/HomePage';

describe('HomePage', () => {
  it('renders the home page with title and call to action', () => {
    // Arrange
    render(<HomePage />);
    
    // Act - None, just render
    
    // Assert
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    expect(screen.getByText(/plan your trip/i, { exact: false })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /get started/i })).toBeInTheDocument();
  });
  
  it('displays key features section', () => {
    // Arrange
    render(<HomePage />);
    
    // Assert
    const featuresSection = screen.getByText(/key features/i, { exact: false });
    expect(featuresSection).toBeInTheDocument();
  });
  
  it('links to sign up or login page', () => {
    // Arrange
    render(<HomePage />);
    
    // Assert
    const loginLink = screen.getByRole('link', { name: /get started/i });
    expect(loginLink).toHaveAttribute('href', '/login');
  });
});
