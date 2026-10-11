# PUSH_INSTRUCTIONS.md

The repository has not been pushed yet. Its history was cleaned for a first public push
(DECISIONS D-026):

- the author's private notes and the project brief are in `private/`, which is gitignored, and
  they were removed from every commit;
- the old build logs (`logs/`), which contained a local path, were removed from every commit;
- every commit and the tag use the identity
  `Mohammad Ari Alexander Aziz <228153893+13222093@users.noreply.github.com>`
  (the GitHub noreply address of the account `13222093`);
- the annotated tag `v1.0.0` points to the current head of `main`;
- `refs/` (the paper and SI PDFs) is gitignored and was never committed.

A full copy of the repository from before the cleaning is in the sibling folder
`corruption-term-limits_backup_2026-10-12_pre-filter`. It still contains the old history, so never
push from it. Delete it once the push has been checked.

## Quick check before pushing
Run these in the repository folder. The first should print only the noreply identity, the
second only `v1.0.0`, and the third nothing.

```bash
git log --all --format="%an <%ae> | %cn <%ce>" | sort -u
git tag
git status --short
```

## Option A: with the GitHub CLI
Install it (for example `winget install --id GitHub.cli`), open a new terminal in the repository
folder, and run:

```bash
gh auth login
gh repo create corruption-term-limits --public --source . --remote origin --push
git push origin v1.0.0
```

## Option B: without the GitHub CLI
Create an empty public repository named `corruption-term-limits` on github.com under the account
`13222093` (no README, license or .gitignore), then run:

```bash
git remote add origin https://github.com/13222093/corruption-term-limits.git
git push -u origin main
git push origin v1.0.0
```

Only `main` and the tag need to be pushed. The local branch `si-verification` is already merged
into `main`.

Optionally, create a GitHub release from the tag (Releases, Draft a new release, choose `v1.0.0`)
and paste the tag message (`git tag -n20 v1.0.0`) as the release note.

## After pushing
1. Replace the placeholder repository URL in the Citation section of `docs_src/README.md.in`, in
   the Data and code availability sections of `paper/main.tex` and `paper/ieee/main_ieee.tex`,
   and in your private CV entry, and add `repository-code: <URL>` to `CITATION.cff`.
2. Regenerate the documents and papers, commit and push:

```bash
make docs paper
git commit -am "Add repository URL"
git push
```

On Windows, use `mingw32-make docs paper`, or run `python experiments/make_numbers.py full`,
`python experiments/make_changes_si.py`, `python experiments/render_docs.py` and
`python experiments/build_paper.py`.
