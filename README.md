![website status](https://img.shields.io/website?url=https%3A%2F%2Ftranslations.python.org&logoColor=yellow&label=website%20status)
[![lint](https://github.com/python-docs-translations/dashboard/actions/workflows/lint.yml/badge.svg)](https://github.com/python-docs-translations/dashboard/actions/workflows/lint.yml)

This project generates a dashboard presenting the Python documentation translations projects available at [translations.python.org](https://translations.python.org).

There are two entrypoints:
- `generate.py`: Generates dashboard HTML and JSON files.
- `generate_build_details.py`: Generates the build details HTML file and log files for each translation project.

Build details downloads pospell results from each translation repository's
`spellcheck-<language-code>` Actions artifact, containing `spellcheck.json` in the
schema version 1 described in `python-docs-pl/SPELLCHECK_REPORT.md`.
Set `GH_TOKEN` (or `GITHUB_TOKEN`) to a token able to read those Actions artifacts
when running locally. The update workflow uses `SPELLCHECK_REPORTS_TOKEN` when
configured, falling back to its GitHub token. A separate token needs Actions read
access to the translation repositories whose artifacts it downloads.
Only complete reports from completed push, schedule, or manual runs in the same
repository and translation branch are used, including runs that failed because
they found spelling issues. The count is the number of PO entries with findings,
and links to `warnings-pospell-<language-code>.txt`, with suspect words, entry
identities, and report provenance. Missing, expired, invalid, or inaccessible
reports are shown as unavailable. Reports can predate the current checkout.

The same report is published unchanged at
`https://translations.python.org/spellcheck-<language-code>.json` for consumers such
as `potodo-docs-priority`. The file contains JSON `null` when no usable report is
available, replacing any previously published report. Consumers need no GitHub
token; only this dashboard downloads Actions artifacts.
