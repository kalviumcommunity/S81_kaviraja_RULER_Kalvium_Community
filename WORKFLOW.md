# Data Workflow Documentation

This repository contains the setup and workflow guidelines for the Data Product team.

## Branching Strategy

Our team follows a strict branching strategy to ensure stable releases and organized collaboration:
- **Main Branch**: The `main` branch holds releasable code only. All code in `main` should be fully tested and production-ready.
- **Feature Branches**: All new work must happen on feature branches. Feature branches must follow the naming convention `[type]/[description]` (e.g., `feature/data-ingestion`, `fix/validation-logic`, `docs/data-dictionary`).
- **Branch Cleanup**: Branches must be deleted automatically or manually after their corresponding Pull Request is merged.

## Commit Message Convention

To maintain a clean and understandable history, we follow Conventional Commits:
- **Types used**: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`.
- **Format**: `[type]: [description]`
  - Example: `feat: add data validation function`
- **Why**: This approach enables automated changelog generation, makes git history clear, and helps developers understand what a commit does at a glance.

## PR Review Process

Code reviews are a critical part of our workflow to maintain code quality:
- **Approvals**: Pull Requests require at least one approval from a team member before they can be merged.
- **Review Focus**: Code review focuses on correctness, code clarity, data integrity, and adequate test coverage.
- **Commit Messages**: Commit messages are reviewed as part of the PR to ensure they follow our convention.

## GitHub Issue Tracking

We use GitHub Issues to plan and track our work:
- **Issue Driven**: Every new feature or bug fix must start with an issue.
- **Details**: Issues must have appropriate labels, assignees, and clear, actionable descriptions.
- **Closing**: Issues are automatically closed when the corresponding Pull Request is merged.
