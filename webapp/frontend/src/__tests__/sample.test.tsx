import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

describe('Sample Test', () => {
  it('should render a basic element', () => {
    render(<div>Hello Vitest</div>);
    expect(screen.getByText('Hello Vitest')).toBeInTheDocument();
  });
});
