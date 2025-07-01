---
file: .github/copilot-instructions.md
purpose: LLM-context injection for repository-specific grounding
audience: GitHub Copilot / LLM agents
scope: High-signal summary of conventions, architecture, and boilerplate
format: Markdown (token-optimized)
---

# Repository Context for GitHub Copilot

## ⚙️ Architecture & Stack

**Purpose:** AI-powered platform transforming multi-family group trip planning into streamlined, collaborative experience with intelligent preference aggregation and cost-optimized infrastructure.

**Stack:** FastAPI, Python 3.11, React 18, TypeScript, Tailwind CSS, Fluent UI v9, Cosmos DB, Microsoft Entra ID, Socket.IO, OpenAI GPT-4, Azure Container Apps, GitHub Actions

**Architecture:** Two-layer Azure serverless architecture with persistent data layer (Cosmos DB, Storage, Key Vault, Service Bus) and ephemeral compute layer (Container Apps), family-atomic design pattern, clean architecture with domain-driven design

## 🔤 Naming Conventions

**TypeScript:** camelCase for variables/functions, PascalCase for components/types/interfaces, SCREAMING_SNAKE_CASE for constants, kebab-case for files

**CSS:** Tailwind utility classes with custom theme extensions, BEM methodology for custom classes: .block__element--modifier

**Database:** snake_case for all Cosmos DB containers and properties, family-scoped data with composite keys

## 🎨 Style & Patterns

**Indentation:** 2 spaces
**Line Length:** max 120 characters
**Imports:** Absolute imports from 'src/' directory using Vite resolver
**Asynchronicity:** Prefer async/await over Promises
**State Management:** React hooks for local state, WebSocket service for real-time data
**Component Design:** Functional components with TypeScript interfaces, Fluent UI v9 components
**Type Safety:** Strict TypeScript, Pydantic models for Python, interface-first development

## 🧩 Common Snippets

**API Service:**
```typescript
// Use this pattern for all data fetching services with standard error handling
import { api } from '@/lib/api';

export async function fetchUserData(userId: string) {
  try {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch user data:', error);
    throw error;
  }
}
```

**React Component:**
```typescript
// All components must be functional, use TypeScript, and follow Fluent UI patterns
import React from 'react';
import { makeStyles } from '@fluentui/react-components';

interface ComponentProps {
  className?: string;
  children?: React.ReactNode;
}

const useStyles = makeStyles({
  root: {
    // Fluent UI styling
  }
});

export const MyComponent: React.FC<ComponentProps> = ({ className, children }) => {
  const styles = useStyles();
  return <div className={styles.root}>{children}</div>;
};
```

**Unit Test:**
```typescript
// Use Vitest with @testing-library/react for frontend testing
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

test('renders component', () => {
  render(<MyComponent />);
  expect(screen.getByRole('button')).toBeInTheDocument();
});
```

## 🐞 Known Issues

**Refactor Targets:** backend/complete_cosmos_migration.py (legacy migration script), frontend/src/components/trip/TripItinerary_fixed.tsx (temporary fix), backend/enhanced_validation.py (consolidate with main validation)

**Known Bugs:** None - 100% test reliability (51/51 frontend tests passing), 94.1% architecture compliance validated

**Technical Debt:** PWA offline capabilities at 17.6% completion, optional Memory Lane feature pending, performance monitoring dashboards incomplete
