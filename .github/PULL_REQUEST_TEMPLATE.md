# Pull Request

## Description

<!-- Provide a clear description of what this PR does -->

## Type of Change

<!-- Mark the relevant option with an 'x' -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] New vendor adapter (adds support for a new exchange)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Changes Made

<!-- List the specific changes made in this PR -->

- 
- 
- 

## Related Issues

<!-- Link to related issues using #issue_number -->

Fixes #
Relates to #

## New Vendor (if applicable)

<!-- If this PR adds a new vendor, fill this out -->

- **Vendor Name**: 
- **REST Endpoints**: 
- **WebSocket Channels**: 
- **Products Discovered**: 
- **API Documentation**: 

## Testing

<!-- Describe the testing you've done -->

### Manual Testing

```bash
# Commands run to test
python3 main.py discover --vendor [vendor_name]
python3 main.py export --vendor [vendor_name] --format snake_case
```

### Test Results

```
# Paste output here
```

### Database Verification

```sql
-- Queries run to verify data
SELECT COUNT(*) FROM products WHERE vendor_id = ...;
```

## Checklist

<!-- Mark completed items with an 'x' -->

- [ ] My code follows the project's code style guidelines
- [ ] All functions are under 50 lines
- [ ] All functions have docstrings
- [ ] I have added/updated comments where necessary
- [ ] I have updated the documentation (README, etc.)
- [ ] I have tested my changes with a real API
- [ ] I have verified the database schema is correct
- [ ] I have checked that no sensitive information is committed
- [ ] My changes generate no new warnings or errors
- [ ] I have updated CONTRIBUTING.md if needed

## Screenshots/Output

<!-- If applicable, add screenshots or example output -->

```json
{
  "example": "output"
}
```

## Additional Notes

<!-- Any additional information reviewers should know -->

## For Reviewers

<!-- Help reviewers understand what to focus on -->

**Focus areas:**
- 
- 

**Known limitations:**
- 
- 
