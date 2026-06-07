# Semi-Autonomous Development Workflow

Codex may implement small tasks, add tests, and prepare pull requests. Merge to `main` remains a human-controlled action because this project contains engineering calculations.

## Cycle

1. Create or select a GitHub Issue.
2. Ask Codex to implement exactly one task.
3. Codex creates a branch named `codex/<short-task-name>`.
4. Codex commits changes and opens a Pull Request.
5. CI runs `ruff` and `pytest`.
6. User reviews the PR summary and merges only if checks pass.

## First Tasks

1. Implement robust `FrameGeometry` validation.
2. Implement CSV loading for the section catalog.
3. Implement SP 20 load-case data models.
4. Implement LIRA export import validation.
5. Implement baseline top-N section recommender.
