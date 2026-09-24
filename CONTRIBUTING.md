# Contributing

## Workflow

1. Open an issue describing the change.
2. Create a branch from `main`: `feat/<name>`, `fix/<name>` or `docs/<name>`.
3. Make small, focused commits.
4. Open a pull request that references the issue (`Closes #<number>`).
5. Merge once CI passes.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/): a short imperative subject, at most 72 characters.

```
feat(header): add mega menu for men and women
fix(cart): keep quantity when drawer closes
```

## Before opening a PR

```bash
pnpm lint
pnpm test
pnpm build
```
