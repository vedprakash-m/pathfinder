/// <reference types="vitest" />
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import matchers from '@testing-library/jest-dom/matchers';
import '@testing-library/jest-dom/vitest';

// Extend Vitest's expect method with testing-library methods
expect.extend(matchers);

// Clean up after each test case
afterEach(() => {
  cleanup();
});
