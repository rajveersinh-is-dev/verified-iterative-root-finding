# Paper

- `main.tex` — manuscript source.
- `references.bib` — BibTeX references (mirror of the inline bibliography).
- `main.pdf` — compiled manuscript (generated with Tectonic; see below).

## Build

```bash
cd paper
tectonic main.tex
```

Tectonic 0.17 was used; no local TeX distribution is required beyond
Tectonic itself. Compilation produces `main.pdf`.
