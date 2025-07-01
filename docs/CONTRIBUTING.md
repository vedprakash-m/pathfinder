# Contributing to Pathfinder

Thank you for your interest in contributing to Pathfinder! This document outlines the guidelines and process for contributing to our AI-powered group trip planner.

## 🎯 Project Overview

Pathfinder is an open-source project licensed under the GNU Affero General Public License v3 (AGPLv3). We welcome contributions from developers, designers, testers, and documentation writers.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Guidelines](#contribution-guidelines)
- [Code Style and Standards](#code-style-and-standards)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)
- [License Agreement](#license-agreement)
- [Dependency Management](#-dependency-management)

## 🤝 Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:

- Be respectful and considerate in all interactions
- Focus on constructive feedback and collaboration
- Respect different viewpoints and experiences
- Report any unacceptable behavior to the project maintainers

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ (for frontend development)
- **Python** 3.9+ (for backend development)
- **Docker** and **Docker Compose** (for local development)
- **Git** for version control

### Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pathfinder.git
   cd pathfinder
   ```
3. **Set up the development environment**:
   ```bash
   # Install frontend dependencies
   cd frontend
   npm install
   
   # Install backend dependencies
   cd ../backend
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   ```

## 🛠 Development Setup

### Running Locally

1. **Start the development stack**:
   ```bash
   docker-compose up -d
   ```

2. **Frontend development**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Backend development**:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📝 Contribution Guidelines

### Types of Contributions

We welcome several types of contributions:

- **🐛 Bug fixes**: Fix issues in existing functionality
- **✨ New features**: Add new capabilities to the platform
- **📚 Documentation**: Improve or add documentation
- **🧪 Tests**: Add or improve test coverage
- **🎨 UI/UX improvements**: Enhance user interface and experience
- **⚡ Performance optimizations**: Improve application performance
- **🔒 Security enhancements**: Address security vulnerabilities

### Before You Start

1. **Check existing issues** to see if your idea is already being worked on
2. **Create an issue** to discuss major changes before implementing
3. **Join our community discussions** for questions and collaboration
4. **Review the project roadmap** to understand current priorities

### Issue Guidelines

When creating issues:

- Use clear, descriptive titles
- Provide detailed descriptions with steps to reproduce (for bugs)
- Include relevant labels (bug, enhancement, documentation, etc.)
- Add screenshots or code examples when helpful
- Reference related issues or pull requests

## 🎨 Code Style and Standards

### Frontend (TypeScript/React)

- **Framework**: React 18+ with TypeScript
- **Linting**: ESLint with TypeScript rules
- **Formatting**: Prettier
- **Style**: Tailwind CSS for styling
- **Testing**: Jest + React Testing Library

```bash
# Run linting
npm run lint

# Run formatting
npm run format

# Type checking
npm run type-check
```

### Backend (Python/FastAPI)

- **Framework**: FastAPI with Python 3.9+
- **Linting**: flake8 or pylint
- **Formatting**: black + isort
- **Type hints**: Required for all functions
- **Testing**: pytest

```bash
# Run formatting
black .
isort .

# Run linting
flake8 .

# Type checking
mypy .
```

### General Standards

- **Commit messages**: Use conventional commits format
  ```
  feat: add trip recommendation algorithm
  fix: resolve authentication timeout issue
  docs: update API documentation
  test: add unit tests for trip planner
  ```
- **Branch naming**: `feature/description`, `fix/description`, `docs/description`
- **Code comments**: Write clear, helpful comments for complex logic
- **Function documentation**: Include docstrings for all public functions

## 🧪 Testing Requirements

### Frontend Testing

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run e2e tests
npm run test:e2e
```

**Requirements**:
- Unit tests for components and utilities
- Integration tests for critical user flows
- Minimum 80% code coverage for new features

### Backend Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_specific.py
```

**Requirements**:
- Unit tests for all business logic
- Integration tests for API endpoints
- Database tests for data operations
- Minimum 80% code coverage for new features

### Test Guidelines

- Write tests before or alongside new features (TDD encouraged)
- Include edge cases and error scenarios
- Use descriptive test names
- Mock external dependencies appropriately
- Ensure tests are deterministic and can run in any order

## 📤 Submitting Changes

### Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Write tests** for your changes

4. **Run the test suite** to ensure everything passes

5. **Commit your changes** with clear, descriptive messages

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a pull request** on GitHub

### Pull Request Guidelines

- **Title**: Clear, descriptive title summarizing the change
- **Description**: Detailed description of what and why
- **References**: Link to related issues
- **Screenshots**: Include UI changes if applicable
- **Checklist**: Use the PR template checklist
- **Breaking changes**: Clearly document any breaking changes

### PR Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or documented)
```

## 👀 Review Process

### What to Expect

1. **Automated checks**: CI/CD will run tests and linting
2. **Maintainer review**: A project maintainer will review your PR
3. **Community feedback**: Other contributors may provide feedback
4. **Iteration**: You may need to make changes based on feedback
5. **Approval**: Once approved, your PR will be merged

### Review Criteria

- Code quality and adherence to standards
- Test coverage and quality
- Documentation completeness
- Performance considerations
- Security implications
- Backward compatibility

## 📄 License Agreement

### Important: AGPLv3 License Terms

By contributing to Pathfinder, you agree that:

1. **Your contributions will be licensed under AGPLv3**: All code contributions become part of the AGPLv3-licensed codebase

2. **Copyright assignment**: You retain copyright to your contributions, but grant the project the right to use them under AGPLv3

3. **Original work**: You confirm that your contributions are your original work or you have proper rights to submit them

4. **License compatibility**: Any third-party code you include must be compatible with AGPLv3

5. **Source code disclosure**: You understand that AGPLv3 requires source code disclosure for network services

### Contributor License Agreement (CLA)

For significant contributions, you may be asked to sign a Contributor License Agreement (CLA) to clarify the intellectual property license granted with your contributions.

### Third-Party Dependencies

When adding new dependencies:

- Ensure they are compatible with AGPLv3
- Document the license in the appropriate package files
- Avoid GPL-incompatible licenses (e.g., Apache 2.0 with patents clause)

## 📦 Dependency Management

Pathfinder uses a comprehensive dependency validation system to ensure CI/CD reliability and prevent environment inconsistencies.

### Adding New Dependencies

When adding new Python packages:

1. **Install the package**:
   ```bash
   pip install package-name==version
   ```

2. **Add to requirements.txt** with pinned version:
   ```bash
   echo "package-name==version" >> backend/requirements.txt
   ```

3. **Run dependency validation**:
   ```bash
   cd backend && python3 local_validation.py
   ```

### Dependency Validation Features

Our local validation system includes:

- **Undeclared Dependency Detection**: Scans all imports against requirements.txt
- **Standard Library Filtering**: Excludes built-in Python modules
- **Import Name Mapping**: Handles package name differences (e.g., `jwt` → `python-jose`)
- **CI/CD Parity Checks**: Ensures local environment matches CI/CD exactly

### Best Practices

- **Pin versions**: Always specify exact versions in requirements.txt
- **Test locally**: Run `local_validation.py` before committing
- **Document why**: Add comments for non-obvious dependencies
- **Keep minimal**: Only include dependencies actually used in the code

### Common Issues

If you see dependency-related errors:

```bash
# Check for undeclared dependencies
cd backend && python3 local_validation.py

# Verify all imports are declared
python3 -c "
import ast
import subprocess
# This will be caught by local validation
"
```

The validation system will provide specific guidance on:
- Missing dependencies to add to requirements.txt
- Unused dependencies that can be removed
- Version conflicts or compatibility issues

## 🙋‍♀️ Getting Help

### Resources

- **Documentation**: Check the project documentation
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Community**: Join our community channels (Discord/Slack)

### Contact

- **Project Maintainer**: Vedprakash Mishra
- **Repository**: https://github.com/vedprakashmishra/pathfinder
- **Issues**: Use GitHub Issues for bug reports and feature requests

## 🎉 Recognition

We value all contributions! Contributors will be:

- Listed in the project's contributor documentation
- Mentioned in release notes for significant contributions
- Eligible for special contributor recognition in our community

## 📈 Development Roadmap

Check our [project roadmap](https://github.com/vedprakashmishra/pathfinder/projects) to see:

- Current development priorities
- Upcoming features
- Areas where help is needed
- Long-term project vision

---

Thank you for contributing to Pathfinder! Together, we're building the future of AI-powered group trip planning. 🚀

**Remember**: All contributions are subject to the AGPLv3 license terms. By participating in this project, you agree to abide by its terms and help us build an open, collaborative platform that benefits everyone.