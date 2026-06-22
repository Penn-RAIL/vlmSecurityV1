# VLM Radiology Review Dashboard

This repository contains a static GitHub Pages review dashboard for the VLM chest radiograph adversarial-attack experiment.

## Deployable Site

The GitHub Pages payload is in:

```text
docs/
```

It contains:

- `docs/index.html`: the review dashboard with embedded model outputs and extracted outcomes.
- `docs/radiologist_review.csv`: starter review CSV for radiologist adjudication.
- `docs/data/images_raw/normal/`: final raw radiographs used by control, user-prompt, and system-prompt jobs.
- `docs/data/images_attack/image_label_final/`: image-label attack radiographs used by image-channel jobs.

The full experiment archive, virtual environment, raw JSONL outputs, local result files, and generated experiment folders are intentionally ignored by Git.

## Rebuild the Pages Site

Run this after changing the corrected outcomes, raw outputs, or review dashboard template:

```bash
python3 NewStuff/src/build_github_pages_review_site.py
```

## GitHub Pages Setup

From this folder:

```bash
git init
git add .gitignore README.md docs NewStuff/src/build_review_dashboard.py NewStuff/src/build_github_pages_review_site.py
git commit -m "Add radiologist review dashboard"
```

Create a GitHub repository, then push:

```bash
git branch -M main
git remote add origin git@github.com:YOUR_USER_OR_ORG/YOUR_REPO.git
git push -u origin main
```

In GitHub:

1. Open the repository.
2. Go to `Settings` -> `Pages`.
3. Under `Build and deployment`, choose `Deploy from a branch`.
4. Select branch `main`.
5. Select folder `/docs`.
6. Save.

The public review link will be:

```text
https://YOUR_USER_OR_ORG.github.io/YOUR_REPO/
```

## Review Workflow

The dashboard is static. It cannot write reviewer decisions back to GitHub by itself.

Recommended workflow:

1. Send each radiologist the GitHub Pages link.
2. They review rows in the browser.
3. They click `Download review CSV`.
4. They send the downloaded CSV back by email, Google Drive, or another approved channel.
5. You merge the returned CSVs locally.

## Data-Sharing Warning

Do not publish the Pages site until you are sure the radiographs, embedded labels, and raw model outputs are allowed to be shared publicly. GitHub Pages sites are internet-accessible, so use an approved private/internal hosting workflow if the review data should not be public.
