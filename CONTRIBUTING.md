# Contributing to NEXARIS Adaptive Scenario Engine (NASE)

Thank you for your interest in contributing to the NEXARIS Adaptive Scenario Engine! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with the following information:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any relevant logs or screenshots
- Your environment (OS, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for enhancements! Please create an issue with:

- A clear, descriptive title
- A detailed description of the proposed enhancement
- Any relevant examples or mockups
- Why this enhancement would be useful to most users

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Create a new Pull Request

#### Pull Request Guidelines

- Follow the existing code style
- Include tests for new features
- Update documentation as needed
- Keep pull requests focused on a single topic
- Reference any relevant issues

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/devartix0aymane/NEXARIS-NASE.git
   cd NEXARIS-NASE
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. Run tests
   ```bash
   pytest
   ```

## Coding Standards

- Follow PEP 8 style guidelines
- Write docstrings for all functions, classes, and modules
- Use type hints where appropriate
- Keep functions and methods focused on a single responsibility
- Write clear, descriptive variable and function names

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.

## Questions?

If you have any questions about contributing, please open an issue or contact the maintainers.

Thank you for your contributions!