# Output files

## The folder

`-o, --output` is the folder to write into: the current folder by default. It is
created if it does not exist, including parent folders:

```bash
templify render -t team.md -d employees.xlsx -o reports/2026/november
```

## File names

| Situation | Result |
|-----------|--------|
| default mode or `--object`, no `-f` | Named after the template: `team.md` → `team.md` |
| `-f "2024 team"` | `2024 team.md` |
| `--each`, no `-n` | `template-1.txt`, `template-2.txt`, ... |
| `--each -n name` | `Rama.txt` |
| `--each -n name --numbered` | `3 - Rama.txt` |
| The `-n` column is empty or missing for a row | That row falls back to `template-<n>.txt` |
| The value has invalid characters: `a/b:c?` | They become `_`: `a_b_c_.txt` |
| The value is a number: `-n id` | `42.txt` |
| `--each` with `--group-by` and `-n department` | One file per group: `IT.html`, `Sales.html` |

The extension always comes from the template.

- `<n>` and `--numbered` count rows **after** ordering and filtering, starting at 1.
- `--numbered` keeps files in data order in a file browser. Combine it with `--order`.

## Never overwriting

templify **never overwrites a file**. If the target exists, the new file gets a short
random suffix:

```text
$ templify render -t team.md -d employees.xlsx -o reports
File generated successfully: .../reports/team.md

$ templify render -t team.md -d employees.xlsx -o reports
File generated successfully: .../reports/team-3f9a1c2e.md
```

That keeps earlier results safe, but it also means a re-run piles up files. Render
into a new or empty folder (for example a dated one) when you want a clean set.

!!! tip "Names that are not unique"
    With `-n name`, two people called Rama do not overwrite each other: the second file
    becomes `Rama-<suffix>.docx`. For predictable names, use a unique column such as an
    id or email, or add `--numbered`.

## What a successful run prints

| Mode | Message |
|------|---------|
| default, `--object` | `File generated successfully: <full path>` |
| `--each` | a progress bar, then `<n> files generated successfully in: <folder>` |
