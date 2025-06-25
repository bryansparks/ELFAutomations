# Pre-commit Hook Issues - Analysis and Solutions

## Current Issues Blocking Commits

### 1. Large Files (package-lock.json)
The `check-added-large-files` hook is blocking commits because of large package-lock.json files.

**Locations:**
- `/package-lock.json`
- `/third-party/agentgateway/ui/package-lock.json`
- `/third-party/kagent/ui/package-lock.json`
- Multiple other package-lock.json files

### 2. YAML Validation Errors
The `check-yaml` hook may be failing on Kubernetes/Helm YAML files that use custom tags or non-standard formatting.

### 3. Third-party Submodules
The presence of `third-party/kagent` as a modified submodule may be causing issues.

## Immediate Solutions

### Option 1: Quick Bypass (Recommended for urgent commits)
```bash
# Commit without running pre-commit hooks
git add -A
git commit --no-verify -m "Your commit message"
git push
```

### Option 2: Selective Hook Bypass
```bash
# Skip specific problematic hooks
SKIP=check-yaml,check-added-large-files git commit -m "Your message"
```

### Option 3: Temporary Disable Pre-commit
```bash
# Uninstall pre-commit hooks
pre-commit uninstall

# Make your commits
git add -A
git commit -m "Your message"
git push

# Reinstall later
pre-commit install
```

## Permanent Solutions

### Solution 1: Configure Pre-commit to Exclude Files

Update `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        exclude: ^(third-party/|old/|venv/|node_modules/)

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        exclude: ^(third-party/|old/|venv/|node_modules/)

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
        exclude: ^(third-party/|old/|venv/|node_modules/)
      - id: end-of-file-fixer
        exclude: ^(third-party/|old/|venv/|node_modules/|.*\.json$)
      - id: check-yaml
        exclude: ^(third-party/|k8s/|helm/|agent-configs/)
        args: ['--unsafe']  # Allow custom tags
      - id: check-added-large-files
        args: ['--maxkb=2048']  # Increase to 2MB
        exclude: 'package-lock\.json|yarn\.lock'
      - id: check-merge-conflict
```

### Solution 2: Use Git LFS for Large Files

```bash
# Install Git LFS
brew install git-lfs  # macOS
git lfs install

# Track large files
git lfs track "*.json"
git lfs track "package-lock.json"
git lfs track "yarn.lock"

# Add .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

### Solution 3: Add to .gitignore

Add these to `.gitignore`:
```
# Large generated files
package-lock.json
yarn.lock
node_modules/

# Submodules with issues
third-party/kagent
third-party/agentgateway
```

## Diagnostic Commands

```bash
# See what pre-commit is complaining about
pre-commit run --all-files --verbose

# Check which files are too large
find . -type f -size +500k -not -path "./.git/*" | xargs ls -lh

# Validate YAML files
find . -name "*.yaml" -o -name "*.yml" | xargs -I {} sh -c 'echo "Checking: {}" && python -c "import yaml; yaml.safe_load(open('\''{}'\'').read())"'

# Check git status
git status
git diff --staged

# See pre-commit version
pre-commit --version
```

## Recommended Approach

1. **For immediate unblocking**: Use `git commit --no-verify`
2. **For long-term**: Update `.pre-commit-config.yaml` with exclusions
3. **For package-lock.json**: Either:
   - Add to `.gitignore` (if not needed in repo)
   - Use Git LFS
   - Increase pre-commit file size limit

## Reset and Reconfigure

If pre-commit is completely broken:

```bash
# Complete reset
pre-commit uninstall
pre-commit clean
rm -rf ~/.cache/pre-commit

# Reinstall
pip install --upgrade pre-commit
pre-commit install
pre-commit run --all-files
```

## Team Workflow Recommendation

Consider using a staged approach:
1. Developers use `--no-verify` during active development
2. Run full pre-commit checks before PR/merge
3. Use CI/CD for enforcement rather than local hooks

This maintains code quality without blocking productivity.