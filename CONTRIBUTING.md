# Contributing to Auto Semantic Project

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/auto_semantic_project.git
   cd auto_semantic_project
   ```

2. **Install Dependencies**
   ```bash
   make install
   ```

3. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Code Style

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to functions and classes
- Maximum line length: 120 characters

```python
def my_function(param: str) -> Dict[str, Any]:
    """
    Brief description of function.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    pass
```

### JavaScript/React (Frontend)
- Use functional components with hooks
- Follow ESLint configuration
- Use meaningful variable names
- Add comments for complex logic

```javascript
// Good
const handleUserQuery = async (question) => {
  // Implementation
};

// Avoid
const f = async (q) => {
  // Implementation
};
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Pull Request Process

1. **Update Documentation**
   - Update README.md if adding new features
   - Add comments to complex code
   - Update QUICKSTART.md if changing setup process

2. **Test Your Changes**
   - Ensure all tests pass
   - Test manually in development environment
   - Check for console errors

3. **Commit Messages**
   Use conventional commit format:
   ```
   feat: add new feature
   fix: resolve bug
   docs: update documentation
   refactor: code refactoring
   test: add tests
   chore: maintenance tasks
   ```

4. **Submit PR**
   - Provide clear description of changes
   - Reference any related issues
   - Add screenshots for UI changes

## Areas for Contribution

### High Priority
- [ ] Add unit tests for backend modules
- [ ] Add integration tests
- [ ] Improve error handling
- [ ] Add support for more databases
- [ ] Performance optimizations

### Documentation
- [ ] Add more example queries
- [ ] Create video tutorials
- [ ] Expand troubleshooting guide
- [ ] Add architecture diagrams

### Features
- [ ] Multi-table joins support
- [ ] Query history and favorites
- [ ] Export results to CSV/Excel
- [ ] Data visualization charts
- [ ] User authentication
- [ ] Query caching

### UI/UX
- [ ] Dark mode support
- [ ] Responsive mobile design
- [ ] Keyboard shortcuts
- [ ] Query suggestions/autocomplete
- [ ] Better error messages

## Project Structure

```
auto_semantic_project/
├── backend/              # Python FastAPI backend
│   ├── sql_agent.py     # Main API server
│   ├── db_connector.py  # Database connection
│   ├── prompts.py       # OpenAI prompts
│   └── ...
├── frontend/            # Next.js frontend
│   └── pages/
│       └── index.js     # Main UI
└── ...
```

## Key Components

### Backend Flow
1. User question received via `/ask` endpoint
2. Question + semantic layer sent to OpenAI
3. OpenAI generates SQL
4. SQL validated against semantic layer
5. SQL executed on database
6. Results returned to frontend

### Semantic Layer
- Defines allowed tables and columns
- Specifies dimensions vs measures
- Contains derived measures
- Enforces data access rules

## Adding New Features

### Adding a New API Endpoint

```python
# In backend/sql_agent.py
@app.get("/new-endpoint")
async def new_endpoint():
    """Endpoint description."""
    return {"result": "data"}
```

### Adding UI Components

```javascript
// In frontend/pages/index.js or new component file
const NewComponent = () => {
  return <div>New Component</div>;
};
```

### Extending Semantic Layer

```python
# In backend/inference_engine.py
# Add new inference rules in infer_for_model()
if 'new_column_pattern' in colset:
    inferred['derived_measures'].append({
        'name': 'new_measure',
        'expression': 'SQL_EXPRESSION',
        'type': 'type',
        'description': 'Description'
    })
```

## Database Support

Currently supported:
- PostgreSQL
- MySQL
- SQLite

To add support for new databases:
1. Update `db_connector.py` with dialect-specific handling
2. Test connection string formats
3. Update documentation
4. Add example to README

## Security Considerations

When contributing, keep in mind:
- Never commit `.env` files
- SQL validation is critical - maintain whitelist approach
- Only SELECT queries should be allowed
- Sanitize all user inputs
- Use parameterized queries where applicable

## Getting Help

- Check existing issues and PRs
- Join discussions in GitHub Discussions
- Ask questions in issues with `question` label
- Review documentation in README.md

## Code Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address review comments
4. Maintainer will merge when approved

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing! 🎉



