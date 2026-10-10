# Clusters

A cluster is one cause of documentation change with all the pages it touches. gypsy proposes a
cluster as an issue; a person confirms it; `draft.py --cluster` drafts every page on one branch
and opens one pull request that closes the issue. All pages merge together.

| Key | Meaning |
|---|---|
| `title` | The cause, in a few words. Title of the issue and of the pull request. |
| `issue` | Number of the issue in this repository that the pull request closes. |
| `prs` | Upstream pull requests delivered in full: every page they change is in the cluster. |
| `partial` | Upstream pull requests with a different cause that also change a rewritten page. Only that effect is delivered here. The value says where the rest goes. |
| `pages.reference` | Pages already current. The drafter reads them and does not change them. |
| `pages.generated` | Pages that a tool writes from the FreeCAD source: `{page, command}`. The tool runs first, and the drafter reads the result. |
| `pages.rewrite` | Pages rewritten to STYLE.md for all of `prs` and `partial`. Whole-page lint. |
| `pages.new` | Pages that do not exist yet. |
| `pages.amend` | Pages that belong mostly to other work. Only what `prs` make false or missing is changed; lint counts the changed lines only. |
| `nav` | Lines to add to `modules/ROOT/nav.adoc` for new pages, each after the line that holds `after`. |
| `facts` | Fact files given to the drafter. |
| `decisions` | What the person decided in the confirmation of the issue, one sentence each. Every draft of the cluster gets them as binding rules. |

A page is the unit of conflict: two clusters that share a page are drafted one after the other.
For work after the backlog, a cluster is one upstream pull request.
