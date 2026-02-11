# Contributing to Parametric Insurance Demo

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/parametric-insurance-demo/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, Azure region)
   - Screenshots if applicable

### Suggesting Features

1. Check [existing feature requests](https://github.com/yourusername/parametric-insurance-demo/issues?q=is%3Aissue+label%3Aenhancement)
2. Create new issue with `enhancement` label
3. Describe:
   - The problem it solves
   - Proposed solution
   - Alternative approaches considered

### Pull Requests

1. **Fork** the repository
2. **Create branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes**:
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation
   - Keep commits atomic and well-described
4. **Test** your changes:
   ```bash
   python tests/run_tests.py
   ```
5. **Commit** with clear messages:
   ```bash
   git commit -m "Add: New fraud detection algorithm"
   ```
6. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create Pull Request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots/examples if UI changes

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/parametric-insurance-demo.git
cd parametric-insurance-demo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r setup/requirements.txt

# Install dev dependencies
pip install pytest black flake8 mypy
```

## Code Style

### Python
- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for functions and classes

```python
def calculate_payout(duration: int, threshold: int, rate: float) -> float:
    """
    Calculate insurance payout based on outage duration.
    
    Args:
        duration: Outage duration in minutes
        threshold: Policy threshold in minutes
        rate: Hourly payout rate
    
    Returns:
        Calculated payout amount
    """
    if duration <= threshold:
        return 0.0
    
    hours_over = (duration - threshold) / 60
    return hours_over * rate
```

### Formatting
Run before committing:
```bash
black shared/ functions/ demo/
flake8 shared/ functions/ demo/
mypy shared/ functions/ demo/
```

## Testing

### Writing Tests
- Add tests for new features
- Update tests for changed functionality
- Aim for >80% code coverage

```python
def test_payout_calculation():
    """Test payout calculation logic"""
    assert calculate_payout(180, 120, 500) == 500.0
    assert calculate_payout(90, 120, 500) == 0.0
```

### Running Tests
```bash
# All tests
python tests/run_tests.py

# Specific test
python tests/test_outage_monitor.py

# With coverage
pytest --cov=shared --cov=functions --cov-report=html
```

## Documentation

### Update Documentation For:
- New features
- Changed behavior
- New configuration options
- API changes

### Documentation Files:
- `README.md` - Project overview
- `QUICKSTART.md` - Getting started guide
- `DEPLOYMENT.md` - Deployment instructions
- Inline code comments
- Function docstrings

## Commit Message Format

```
Type: Short description (50 chars max)

Longer description if needed (72 chars max per line)

- Bullet points for multiple changes
- Reference issues: Fixes #123

Type can be:
- Add: New feature
- Fix: Bug fix
- Update: Changes to existing feature
- Docs: Documentation only
- Style: Code style changes
- Refactor: Code restructuring
- Test: Adding/updating tests
- Chore: Maintenance tasks
```

## Areas for Contribution

### Good First Issues
- Documentation improvements
- Adding more demo scenarios
- Improving error messages
- Adding more test coverage

### Feature Requests
- Additional insurance types (flood, earthquake)
- Machine learning claim prediction
- Mobile app for policyholders
- Blockchain audit trail
- Multi-language support

### Code Quality
- Improving test coverage
- Performance optimization
- Error handling improvements
- Code documentation

## Review Process

1. Automated checks must pass (tests, linting)
2. At least one maintainer review required
3. Address review comments
4. Maintainer will merge when approved

## Questions?

- 💬 [GitHub Discussions](https://github.com/yourusername/parametric-insurance-demo/discussions)
- 🐛 [GitHub Issues](https://github.com/yourusername/parametric-insurance-demo/issues)
- 📧 Email: your-email@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
