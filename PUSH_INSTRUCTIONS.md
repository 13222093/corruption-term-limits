# PUSH_INSTRUCTIONS.md

The repository has not been pushed. When the release was prepared, it had no git remote and the
GitHub CLI (`gh`) was not installed, so the automatic push could not run. Branch `main` and the
annotated tag `v1.0.0` are ready locally.

## Before you push: what becomes public
- Every file on `main`, including `SOP_sentences.md`, `NOTES_for_author.md`, `CV_ENTRY.md` and
  `CLAUDE.md`. If you prefer to keep any of them private, remove them with `git rm` and commit
  before pushing.
- The full commit history. Commits carry the name and email set in `git config user.name` and
  `git config user.email` on this computer. Check them with `git log --format="%an <%ae>" | sort -u`.
- Three old build logs (removed from the current tree, still in earlier commits) contain the
  local project path on this computer. To remove them from history as well, use
  `git filter-repo --path logs --invert-paths` before the first push. This changes every commit
  hash, so the `git_commit` fields in `results/full/*.json` and the commit aef9a3f cited in
  CHANGES_SI.md would then point to commits that no longer exist (DECISIONS.md D-023).
- `refs/` (the paper and SI PDFs) is gitignored and was never committed.

## Option A: with the GitHub CLI
Install it (for example `winget install --id GitHub.cli`), open a new terminal in the repository
folder, and run:

```bash
gh auth login
gh repo create corruption-term-limits --public --source . --remote origin --push
git push origin v1.0.0
```

## Option B: without the GitHub CLI
Create an empty public repository named `corruption-term-limits` on github.com (no README,
license or .gitignore), then run, replacing YOUR-GITHUB-USERNAME:

```bash
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/corruption-term-limits.git
git push -u origin main
git push origin v1.0.0
```

Optionally, create a GitHub release from the tag (Releases, Draft a new release, choose
`v1.0.0`) and paste the tag message (`git tag -n20 v1.0.0`) as the release note.

## After pushing
1. Replace the placeholder URL in `docs_src/CV_ENTRY.md.in`, the Citation section of
   `docs_src/README.md.in`, the Data and code availability section of `paper/main.tex` and
   `paper/ieee/main_ieee.tex`, and add `repository-code: <URL>` to `CITATION.cff`.
2. Regenerate the documents and papers and commit:

```bash
make docs paper
git commit -am "Add repository URL"
git push
```

On Windows, use `mingw32-make docs paper` or run `python experiments/make_numbers.py full`,
`python experiments/make_changes_si.py`, `python experiments/render_docs.py` and
`python experiments/build_paper.py`.
