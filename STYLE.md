# CAM documentation style guide

Draft 0.1, 2026-10-01. Baseline derived from the 76 pages on the `audit` branch, the page
conventions in the Antora experiment plan (§8.4), and `src/Mod/CAM/Roadmap/ADR/ADR-000.md`.
This document is the style target for every page written or revised from now on, by a person
or by gypsy. Where the existing pages and this guide disagree, the guide wins and the page is
brought into line when it is next touched.

Normative words: *must*, *must not*, *should*. A *must* is checked at review; a *should* is a
default that a page may depart from with a reason in the pull request.

## 1. Purpose and audience

The documentation describes what the CAM workbench on FreeCAD `main` does today. It is reference
material first: a reader who has a part open and a question about one command, property or dialog
finds the answer on one page. Explanation lives in concept pages; procedure lives in tutorials.
A page does not try to be all three.

The reader is assumed to know FreeCAD's interface (tree view, property view, task panel, report
view) and basic machining terms (feed, spindle, stock, work offset). The page does not teach
either. It links to the FreeCAD wiki for interface topics (§9) and to the glossary for CAM terms.

## 2. Voice and register

- Technical over accessible. State what the software does. Do not persuade, reassure or warn
  about difficulty.
- No analogies, no metaphors, no humour.
- Second person for procedures: "Select the faces. Press **OK**." Declarative present tense for
  description: "The operation cuts along the selected edges." Do not write "the user", "users"
  or "we".
- Active voice. The subject is the operation, the dialog, the property or the reader.
- No history. Do not write "in previous versions", "formerly", "this replaced the X tool". The
  version selector carries the history; a page describes one version. The one exception is a
  deprecation notice (§7).
- No hedging and no filler: "simply", "just", "please", "note that", "it should be noted",
  "as desired", "it is suggested that".
- No forward promises: "will be added", "is planned", "a future version".
- No capitalised emphasis and no exclamation marks. A hazard is a `WARNING:` admonition (§6.5).

## 3. Sentences and paragraphs

Each sentence becomes one translation unit. Write so that a sentence can be translated alone.

- One idea per sentence. About 20 words; 30 is the ceiling.
- A sentence must not depend on the sentence before it for its subject ("It also…", "This…").
  Name the subject again.
- Paragraphs of one to four sentences. A list beats a paragraph that enumerates.
- Numbered list for a sequence of actions. Bulleted list for alternatives or properties.
- Spell out a term the first time it is used on a page, then use the short form if ADR-000 gives
  one (Operation / Op, Tool Controller / TC, Post-Processor / Post).

## 4. Vocabulary

ADR-000 is the normative glossary. Its terms are used exactly, with the capitalisation it gives
(**Job**, **Stock**, **Tool Bit**, **Tool Controller**, **Base Geometry**, **Work Plane**,
**Toolpath**, **Post-Processor**, **Machine**, **Sanity Check**). Its `_Avoid_` lists are
prohibited words in prose. A term's first use on a page links to its glossary entry
(`xref:reference/glossary.adoc#tool-controller[Tool Controller]`).

Rules the current pages break most often, in order of frequency:

| Write | Not | Reason |
|---|---|---|
| Tool Bit, Tool Controller, Tool Library, Tool Shape | tool, toolbit, ToolBit, cutter, bit, end mill | "Tool" alone is not a domain term. The corpus has about 900 bare uses and three spellings of Tool Bit. |
| Toolpath | path, Path, the path | "Path" is a code namespace only. |
| Base Geometry | base, selection, target, input geometry | |
| Operation, Op | step, task, action | |
| Stock | blank, billet, raw material, workpiece | |
| Model | part, workpiece | The thing being machined. |
| Fixture | WCS, work offset, work coordinate system | A Fixture is a G54–G59.9 selection, not clamping. Say so on first use because the industry meaning differs. |
| Work Plane | plane, tilted plane, local coordinate system, indexed frame | |
| Step Down, Step Over | axial stepover, radial stepdown | |
| Horizontal Feed, Vertical Feed, Spindle Speed | feedrate, F-word, rpm (as a name), plunge rate | "Plunge rate" and "cutting speed" are tolerated in prose when the Tool Controller property is named alongside. |
| Post-Processor, Post | post processor, postprocessor, G-code generator, exporter | Hyphenated. The UI label "Post Processor" is quoted as the UI spells it (§4.1). |
| Post-Processing Dialog | post dialog, export dialog | |
| Machine, Machine Template | machine config, machine profile, CNC, controller | |
| Deprecated | legacy, obsolete, retired, old | Only when a Deprecation Notice exists in the code (§7). |
| Strategy | mode, kind, type, pattern | For the choice of algorithm. "Pattern" is reserved for a geometric pattern. |
| Dressup | post-modifier, path filter | |
| Tag | tab | Holding tags. |
| Sanity Check, Squawk | linter, validator, pre-flight check, warning (as the category) | |
| Setup Sheet | defaults, config | Say on first use that it is the Job's defaults container, not the shop document. |

### 4.1 UI strings

A string that appears in the interface is quoted as the interface spells it, even when it
violates ADR-000. "Toolbit Library Manager", "Post Processor", "Operations" and property names
such as `HorizFeed` are UI facts, not prose. Mark them as UI (§6.3) so the reader and the
translator know the spelling is fixed.

Property names are written as the property editor shows them (space-separated, "Final Depth"),
not as the Python attribute ("FinalDepth"), except in the Scripting section and in expressions.

### 4.2 Version words

FreeCAD releases are "1.0", "1.1", "26.3". Development `main` is "26.3dev". Do not write
"v1.1", "FreeCAD 1.1 and later", or a `VersionPlus` range; the selector and the `[.since]`
marker (§6.6) carry version scope.

## 5. Page types and skeletons

Every page is one of four types. The type decides the headings. Headings are level-two (`==`)
in the order given; omit a heading that would be empty, do not add others, and do not rename.

### 5.1 Command page

One page per command in the CAM menu or toolbar: operations, dressups, tool commands, Job
commands, inspect and output commands. Title is the command's menu label without the "CAM "
prefix the wiki used ("Profile", "Dogbone", "Post Process").

```
= Profile
:page-command: CAM_Profile
:page-icon: CAM_Profile.svg
:page-menu: CAM → Profile
:page-toolbar: Basic Operations
:page-shortcut: P, P
:page-since: 0.19
:description: Contour cut along the selected faces or edges, or around the whole Model.

[.fcinfobox]
--
[.fcTitle]
image:CAM_Profile.svg[Profile,32] *Profile*

Menu location:: menu:CAM[Profile]
Workbenches:: xref:index.adoc[CAM]
Default shortcut:: kbd:[P,P]
Introduced in version:: 0.19
See also:: xref:operations/pocket.adoc[Pocket], xref:dressups/tag.adoc[Tags]
--

== Description
== Usage
== Options
== Properties
== Strategies
== Notes and limitations
== Scripting
== Related
```

- **Description**: two to six sentences. What the command produces, what it acts on, what it
  requires (OCL, a Machine with a rotary axis). One figure of a representative result.
- **Usage**: numbered steps from invocation to **OK**. Invocation is one step with the toolbar
  button, menu item and shortcut as sub-bullets. Base Geometry selection and task-panel tabs
  are separate steps.
- **Options**: the task panel, one level-three heading per tab, in the tab order. Each control
  is a bullet: `*Label*: what it does. Values a, b, c. Default: x.`
- **Properties**: one block-titled bullet list per property group, in the property editor's
  order (`.Base`, `.Depth`, `.Heights`, `.Operation`, …). Each property is
  `*Name*: description. Values. Default.` Read-only and expression-driven properties say so.
  Properties already explained under Options are listed with a one-line description and no
  repetition. When a generated partial exists, `include::partial$props/<op>.adoc[]` replaces
  the hand-written list.
- **Strategies**: only when the operation has a `Strategy` property. One level-three heading
  per value.
- **Notes and limitations**: behaviour that is correct but surprising, geometry that is not
  supported, interactions with other commands. Not a FAQ.
- **Scripting**: a runnable example of creating and configuring the object through
  `Path.Op.<Name>.Create`, as on the current Drilling page. Omit for commands with no object.
- **Related**: xrefs to pages the reader is likely to need next. No external links.

### 5.2 Concept page

Explains one idea that several commands share: depths and heights, Work Planes, Tool
Controllers versus Tool Bits, Fixtures, the output pipeline. Headings are free but the first
is `== Overview` and the last is `== Related`. A concept page names the commands that use the
concept and links to them; it does not duplicate their option lists.

### 5.3 Reference page

Preferences, file formats (`.fctb`, `.fcm`, Job Template XML), the Post-Processor catalogue,
the glossary, the experimental-features list. Tabular where the content is tabular. No
procedures.

### 5.4 Tutorial

A complete task from an empty document to posted G-code, with the result shown. Numbered steps
throughout, one screenshot per state change the reader has to recognise. A tutorial names the
FreeCAD version it was recorded against in `:page-since:` and is re-recorded, not patched, when
the interface changes.

## 6. AsciiDoc mechanics

### 6.1 Page attributes

Required on every page: title, `:description:` (one sentence, used by search and link previews).
Required on command pages: `:page-command:`, `:page-icon:`, `:page-menu:`, `:page-toolbar:`,
`:page-since:`. Optional: `:page-shortcut:`, `:page-aliases:` (old wiki file names),
`:page-status:` (§8).

Provenance attributes written by tooling, never by hand: `:page-origin:`,
`:page-origin-revision:`, `:page-imported:`, `:page-audit:`, `:page-source-pr:`.

### 6.2 Cross-references

Always `xref:` with explicit link text; never a bare `<<anchor>>` to another page, never a URL
to the published site. Link text is the page title or the term, not "here" or "this page".
Within a page, `<<section-id,Section title>>`.

### 6.3 Interface elements

| Element | Markup | Example |
|---|---|---|
| Menu path | `menu:` | `menu:CAM[Profile]`, `menu:Edit[Preferences > CAM > Assets]` |
| Button | `btn:` | `btn:[OK]`, `btn:[Add Toolbit…]` |
| Key | `kbd:` | `kbd:[Ctrl+Shift+N]`, `kbd:[P,P]` |
| Property, checkbox, field label | bold | `*Final Depth*` |
| Dialog, tab, panel, group box name | italic | `_Base Geometry_ tab`, `_Suggest Feeds & Speeds_ dialog` |
| Enumeration value, file name, code identifier, expression | monospace | `` `Tapping` ``, `` `.fcm` ``, `` `OpToolDiameter*0.75` `` |
| Toolbar icon inline | `image:` 16 px | `image:CAM_Profile.svg[Profile,16]` |

### 6.4 Lists

Numbered (`.`) for steps. Bulleted (`*`) for everything else. Property groups use a block title
(`.Depth`) over the list. Nest at most two levels. Do not use description lists (`term::`)
outside the infobox.

### 6.5 Admonitions

`NOTE:`, `WARNING:` and `CAUTION:` in the one-line form, at most one of each per section.
`WARNING:` is for damage to the part, the Tool Bit or the Machine. `CAUTION:` is for loss of
work in the document. No `TIP:`, no `IMPORTANT:`, and no imitation admonitions
(`*_Note_*:`, `*NOTE*:`, `Note:` as a plain paragraph).

### 6.6 Version markers

Version-dependent facts carry an inline marker in one fixed form:

```
[.since]#introduced in 26.3#
```

The marker precedes the sentence or the list item it scopes and is followed by a colon when it
scopes a sentence. The current pages use eleven variants of this marker; only this one is valid.
Do not mark anything older than the previous release: the selector exists so that a page
describes one version.

### 6.7 Tables

Pipe tables (`|===`) with a header row, for data that has columns: property name, type, default;
post name, controller family, status. Not for layout, and not for a list that has one column.

### 6.8 Code

`[source,python]` for scripts, `[source,gcode]` for G-code, `[source,json]` for `.fcm` and
`.fctb` content. Every code block runs or parses as shown. No `...` elisions inside a block.

## 7. Deprecated and experimental

An Operation or configuration is documented as deprecated only when the code carries a
Deprecation Notice (`opDeprecationNotice`). The page keeps its full content, moves to
Reference → Obsolete in the navigation, and opens with:

```
WARNING: Deprecated. Superseded by xref:operations/drilling.adoc[Drilling] with
*Strategy* `Tapping`. The command is no longer in the menus; existing objects still load,
recompute and post.
```

An experimental command (listed in Preferences → CAM → Advanced) opens with a `NOTE:` saying
so and linking to `reference/experimental.adoc`. Nothing else on the page changes.

## 8. Stubs and status

A page that exists in the navigation but has not been written to this guide is a stub:

```
= Slot
:page-status: stub

This page has not been written yet. The imported wiki page is at
xref:wiki-2026-08@cam::operations/slot.adoc[Slot (wiki)].
```

`:page-status:` values: `stub`, `draft` (written, not yet reviewed against a running FreeCAD),
`generated` (produced by tooling), empty (reviewed). The build counts them.

## 9. Links outside the component

- FreeCAD interface and core concepts link to the wiki with the canonical page name:
  `https://wiki.freecad.org/Tree_view`, `Property_editor`, `Report_view`, `Task_panel`,
  `Expressions`, `Std_Base`. Spelling is the wiki's; the current pages use both `Tree_View`
  and `Tree_view`.
- Other workbenches link to the wiki page of the workbench.
- External tools (OpenCamLib, CAMotics) link to the project site once, on the page that
  introduces them.
- No links to forum threads, videos, issues or pull requests in page text. Provenance goes in
  the pull request and in `:page-source-pr:`.

## 10. Images

### 10.1 Naming and placement

`modules/ROOT/images/<page>/<what>.png`, lower-case, hyphenated:
`operations/profile/task-panel-operation.png`, `operations/profile/result-contour.png`. Icons
stay in `images/` by their source name (`CAM_Profile.svg`). The wiki-era names
(`Path_profile_example.jpg`) are replaced when the page is rewritten.

### 10.2 What a figure shows

- One figure per concept. A figure is referred to by the sentence before it.
- Alt text is required and describes the content, not the file: `Profile task panel, Operation
  tab, with Side set to Outside`.
- Width: 600 for a 3D view or a full task panel, 400 for a dialog, natural size for an icon.
  Set with `[alt text,600]`, no `width=` attribute.
- Captions are optional and use the `.Caption` block title form.

### 10.3 Capture rules

These rules exist so that captures are reproducible by a script and comparable across versions.

- FreeCAD `main` at the commit named in the pull request, default preferences except as listed,
  light theme, English UI, metric document units.
- 3D view: axis cross off, navigation cube hidden, white background gradient off (plain
  background), isometric view unless the figure is about a plane, fit to the Job's Stock.
- Task panels and dialogs are captured whole, at their default size, with the window frame
  excluded.
- The sample part is one of the documented test models (`models/`), named in the figure's
  manifest entry. A figure that needs geometry the models do not have adds a model; it does not
  use an ad-hoc part.
- PNG, no scaling after capture, no annotation drawn onto the image. Call-outs go in the text.
- Every capture has an entry in `images/manifest.yml`: file, page, model, FreeCAD commit, the
  script or recipe that produced it, and the date. A figure without an entry is replaced when
  its page is next revised.

## 11. Pull requests from gypsy

A gypsy pull request is reviewed like any other. It must:

- change the pages that one upstream pull request affects, and nothing else;
- name the upstream PR in the title and body, and in `:page-source-pr:` on each page it touches;
- state in the body what it changed and what it could not verify, in that order;
- set `:page-status: draft` on a page whose behaviour it described without running it;
- include regenerated figures, with manifest entries, for any control or result it describes
  that it also captured.

## Appendix A. Where the current pages depart from this guide

Measured on `audit`, 2026-10-01. These are the clean-ups a rewrite of each page carries out.

| Departure | Extent |
|---|---|
| Bare "tool" for Tool Bit or Tool Controller | about 900 occurrences |
| "toolbit" / "ToolBit" in prose for Tool Bit | about 200 |
| Eleven spellings of the `[.since]` marker | 360 markers |
| Imitation admonitions (`*_Note_*:`, `*NOTE*:`) | most imported operation pages |
| Titles with the "CAM " prefix and CamelCase (`CAM DressupLeadInOut`) | 70 of 76 titles |
| History and comparison with earlier versions in Description | most imported pages |
| "the user" / "we" | about 60 |
| Images named by wiki convention, no alt text, `width=` attribute | all 42 raster figures |
| Wiki links with inconsistent casing (`Tree_View` / `Tree_view`) | 26 |
| `== Tasks Window Editor Layout`, `== See also`, `== Resources` instead of the skeleton headings | 14 pages |
| Scripting section present but example not runnable | not measured |

## Appendix B. Review checklist

- [ ] Page type and headings match §5.
- [ ] Every ADR-000 term is spelled as ADR-000 spells it; no word from an `_Avoid_` list.
- [ ] UI strings quoted as the UI spells them and marked per §6.3.
- [ ] No sentence over 30 words; no sentence that needs its predecessor.
- [ ] No history, hedging, promises, analogies.
- [ ] `[.since]` markers in the single valid form, none older than the previous release.
- [ ] Every figure: named per §10.1, alt text, manifest entry, captured per §10.3.
- [ ] Every xref resolves; the build has no warnings.
- [ ] Scripting example runs on the FreeCAD commit named in the PR.
