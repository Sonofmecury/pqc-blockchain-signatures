# Publishing checklist — PQC-for-Blockchain preprint

The manuscript (`paper/PQC_Blockchain_Preprint.pdf`), code, data, and figures are
ready. The final upload steps require **your** accounts; this is the exact order.

## 0. Pre-flight (do once, ~30 min)

- [ ] **Register an ORCID** at https://orcid.org (2 min). Put the ID into:
      `CITATION.cff` (uncomment the `orcid:` line) and the manuscript author block.
- [ ] **Decide authorship.** If Dr Seyed Mostafa or Dr Julia contributed/endorse,
      add them as co-authors now (also strengthens the work and unlocks arXiv).
- [ ] **(Recommended) Re-run benchmarks at full N for camera-ready numbers.**
      The SLH-DSA-128s medians used fewer iterations (time-capped). Overnight:
      `bash scripts/run_all.sh 1000 120` then regenerate the PDF (Step 3 below).
      The conclusions won't change; the numbers just become fully N=1000.

## 1. GitHub (hosts the code; ~15 min)

- [ ] Create a public repo, e.g. `github.com/Sonofmecury/pqc-blockchain-signatures`.
- [ ] Fill the two TODOs in `CITATION.cff` (orcid + `repository-code` URL).
- [ ] Push the repository (exclude the heavy build dir):
      ```bash
      cd pqc-blockchain-signatures
      printf "vendor/\n__pycache__/\n*.pyc\n" >> .gitignore
      git init && git add . && git commit -m "PQC-for-blockchain study: code, data, figures, manuscript"
      git branch -M main
      git remote add origin https://github.com/Sonofmecury/pqc-blockchain-signatures.git
      git push -u origin main
      ```
- [ ] Create a GitHub **Release** tagged `v0.1.0` (Zenodo archives releases).

## 2. Zenodo (mints the citable DOI; ~10 min)

- [ ] Sign in to https://zenodo.org **with your GitHub account**.
- [ ] In Zenodo → Settings → GitHub, flip the switch **ON** for the repo.
- [ ] Back on GitHub, publish the `v0.1.0` release. Zenodo auto-archives it and
      issues a **DOI**.
- [ ] Add the DOI badge to the README and the DOI to the manuscript's
      "Data and Code Availability" section, then re-export the PDF (Step 3).

## 3. Re-export the PDF after edits (whenever text/DOI changes)

```bash
cd paper
pandoc main.md -o PQC_Blockchain_Preprint.pdf --pdf-engine=pdflatex \
  -V geometry:margin=1in -V fontsize=11pt -V colorlinks=true -H /tmp/header.tex
```
(The `header.tex` snippet that scales figures is in the repo notes; it sets
`\setkeys{Gin}{width=0.82\linewidth,keepaspectratio}`.)

## 4. TechRxiv (primary preprint home; no endorsement needed; ~20 min)

- [ ] Create an account at https://www.techrxiv.org (IEEE).
- [ ] Upload `paper/PQC_Blockchain_Preprint.pdf`.
- [ ] Title/abstract: copy from the manuscript front-matter.
- [ ] Add the Zenodo DOI + GitHub link in the metadata.
- [ ] Category: Computer Science → Cryptography / Security.
- [ ] Submit. TechRxiv issues its own DOI; the preprint goes live after a light check.

## 5. arXiv (optional, higher prestige; needs endorsement)

- [ ] Create an account at https://arxiv.org.
- [ ] Primary category: **cs.CR** (Cryptography and Security).
- [ ] First-time cs.CR authors need an **endorsement** — ask Dr Seyed Mostafa or
      Dr Julia (or any arXiv-published contact). A co-author who is already an
      arXiv author removes this requirement entirely.
- [ ] arXiv prefers LaTeX source; `paper/main.md` + `refs.bib` convert cleanly via
      `pandoc main.md -o main.tex` if you want to submit source rather than PDF.

## 6. After it's live (~15 min, high leverage for scholarships)

- [ ] Add to your CV / SOP: title, venue, DOI, one-line result
      ("benchmarked ML-DSA/SLH-DSA/Falcon vs ECDSA for blockchains; signature
      size, not CPU, is the binding migration cost").
- [ ] Update your portfolio site (mukhtarabdulrazaq.xyz) and LinkedIn with the link.
- [ ] Link the preprint from the GitHub README.
- [ ] Then (and only then) start the Canada professor outreach — the email's
      "my undergraduate research on post-quantum cryptography" line is now a live,
      citable preprint with code. Lead with Stebila (Waterloo / Open Quantum Safe —
      you used his liboqs), Gorbunov, and Clark.

## What to cite it as

See `CITATION.cff`. After Zenodo, the canonical citation is the DOI; before that,
cite the GitHub URL.
