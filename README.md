# CAM_DOC: FreeCAD CAM documentation, maintained by gypsy

This repository is a personal experiment by one FreeCAD contributor. It is **not** an official
FreeCAD project and does not replace the [FreeCAD wiki](https://wiki.freecad.org/CAM_Workbench).

It publishes the CAM workbench documentation as a versioned site built from git:

- branch `main` — the current documentation, maintained against FreeCAD `main` (26.3dev) and
  published as `DEV`. Seeded 2026-10-01 from the `audit` branch of `sliptonic/freecad-cam-docs`
  (the wiki pages with the 2026-08-22 audit applied);
- branch `wiki` — the wiki's CAM pages, imported mechanically from MediaWiki markup and labelled
  by import date, with the de/fr/pl translations.

`gypsy/` holds the bot that keeps `main` current: it triages every merged `Mod: CAM` pull
request in FreeCAD, drafts the documentation changes to [STYLE.md](STYLE.md), captures figures
from the running application, and opens a pull request here for a person to merge. See
`gypsy/README.md`.

See [PROPOSAL.md](PROPOSAL.md) for what the experiment is trying to show and why.

## Layout

```
antora.yml                 component descriptor (differs per branch)
antora-playbook.yml        site assembly: which branches become which versions
modules/ROOT/              pages, navigation, images, partials (Antora standard layout)
supplemental-ui/           header override that puts the version selector in the header
gypsy/                     triage, lint, prompts, verdicts, bot
tools/                     wiki importer, template handlers, migration report, helpers
.github/workflows/         build, validate, deploy, pull-request previews
```

## Build locally

```
npm ci
npx antora antora-playbook.yml        # output in build/site/
```

`antora-playbook.yml` reads the `wiki` and `main` branches of this clone, so both must exist
locally (`git branch wiki origin/wiki`).

To re-run the wiki import (branch `wiki` only) you need `pandoc` and a clone of the wiki bridge
repository:

```
python3 tools/import_wiki.py --source ../FreeCAD-Documentation-Project/wiki --out modules/ROOT
```

## Licenses

- Documentation content on the `wiki` branch is imported from the FreeCAD wiki and is licensed
  [CC BY 3.0](LICENSE-CONTENT), © the FreeCAD wiki contributors. Rewritten content on `DEV` is
  CC BY 3.0 as well.
- Tooling (`tools/`, CI, UI overrides) is [LGPL-2.1-or-later](LICENSE).
