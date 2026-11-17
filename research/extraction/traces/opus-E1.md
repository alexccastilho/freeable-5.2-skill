# E1: Markdown notes to GitHub Pages CLI, plan

Here's a plan. I've kept v1 small on purpose: turn a folder of `.md` files into a folder of `.html` files that GitHub Pages can serve as-is. Anything past that is listed separately as optional.

## Questions I would ask

1. **Which language or runtime do you want?** Default: **Node.js (TypeScript)**, shipped on npm so `npx notes2site` works. It has the most mature Markdown tooling (remark/rehype or markdown-it).
2. **What do your notes look like?** Plain CommonMark, or Obsidian-style with `[[wikilinks]]`, `![[embeds]]`, YAML front matter and tags? Default: **CommonMark + GFM (tables, task lists) + optional YAML front matter + `[[wikilinks]]`**, because note folders usually have them.
3. **Is the folder flat or nested, and are there images or attachments next to the notes?** Default: **nested folders are allowed, and non-Markdown files get copied over unchanged.**
4. **How do you want to deploy?** (a) push built output to a `gh-pages` branch from your machine, (b) a GitHub Actions workflow that builds on push, or (c) commit to `/docs` on main. Default: **(b), with the CLI generating the workflow file.** The CLI also gets a `build` command that works offline, so you're never tied to Actions.
5. **Will it be served from a project page (`user.github.io/repo/`) or a user/custom domain (`user.github.io` / `notes.example.com`)?** This decides the base path. Default: **project page, so every link must respect a configurable `basePath`.**
6. **Are there notes that must not be published?** Default: **skip any note with `draft: true` or `publish: false` in front matter, plus anything matched by an ignore file.** Publishing private notes by accident is the worst failure this tool can have.
7. **How much design do you want?** Default: **one clean built-in theme, overridable with a single template folder.** No theme marketplace.

## What v1 does (scope)

```
notes2site build <notesDir> [--out dist] [--base-path /repo/] [--config notes2site.config.json]
notes2site serve <notesDir>        # build + local preview with live reload
notes2site init-gh-actions         # writes .github/workflows/pages.yml
```

- Every `notes/foo/bar.md` becomes `dist/foo/bar/index.html`, for clean URLs that work on Pages without server rewrites.
- Index page: `index.md` if there is one, otherwise a generated list of notes grouped by folder.
- Wikilinks and relative `.md` links are rewritten to the right site URLs. Broken links are reported as warnings, and `--strict` turns them into errors.
- Assets (images, PDFs) are copied, keeping their relative paths.
- Title comes from front matter `title`, then the first `# H1`, then the filename.
- Writes `.nojekyll`, so Pages doesn't run Jekyll and drop `_underscored` files.
- Optional `CNAME` written from config.
- Sitemap and a basic 404.html.

**Out of scope for v1:** search, tags pages, backlinks, RSS, math/mermaid, incremental builds. All are listed under Later.

## Architecture

```
src/
  cli.ts            # arg parsing (commander), wires commands
  config.ts         # load + validate config (defaults < file < flags)
  scan.ts           # walk notesDir, apply ignore rules, classify md vs asset
  parse.ts          # front matter (gray-matter) + markdown -> HAST (unified/remark/rehype)
  links.ts          # build slug map; resolve [[wikilinks]] and relative links; collect broken links
  render.ts         # HAST -> HTML inside a layout template
  write.ts          # write output, copy assets, .nojekyll, CNAME, sitemap
  serve.ts          # local static server + file watcher (chokidar) + rebuild
  templates/        # default layout.html, style.css
  gh/pages.yml      # Actions workflow template
```

The pipeline is two passes: **scan + parse everything → build the slug/link map → render and write.** Links need the second pass because a link can only be resolved once every page's final URL is known.

Key decisions:
- **Slugs:** lowercased, spaces become `-`, unicode kept. Two notes that end up with the same slug are a hard error that names both files. Never overwrite silently.
- **HTML safety:** turn raw HTML in notes off by default, or sanitize it with rehype-sanitize. Notes copied from the web can carry script tags.
- **Deterministic output** (sorted traversal, no timestamps in the HTML) keeps diffs on `gh-pages` meaningful.
- **Base path** is applied in exactly one place (the URL builder in `links.ts`) and used everywhere, including the CSS/asset links in the template.

## Deploy path (default: GitHub Actions)

`init-gh-actions` writes a workflow that checks out the repo, runs `npx notes2site build notes --base-path /${{ github.event.repository.name }}/`, then uses `actions/upload-pages-artifact` + `actions/deploy-pages`. The user sets Settings → Pages → Source = "GitHub Actions" once, and the CLI prints that instruction.

## Implementation order

1. Skeleton CLI + config loading + `build` that converts a flat folder (no links). Test against a fixture folder.
2. Nested folders, clean URLs, asset copying, `.nojekyll`.
3. Link map: relative `.md` links, then wikilinks (`[[Note]]`, `[[Note|alias]]`, `[[Note#Heading]]`), plus broken-link reporting.
4. Draft/ignore filtering, with tests that prove a draft never reaches `dist/`.
5. Default theme + generated index + 404 + sitemap.
6. `serve` with watch/live reload.
7. `init-gh-actions` + README with a 5-minute quickstart.
8. Publish to npm.

## Testing

- **Fixture-based snapshot tests:** a `test/fixtures/notes/` tree with an expected `dist/` tree. Covers nested folders, wikilinks, a broken link, a draft, an image, a slug collision, and unicode filenames.
- **Unit tests** for slugging and link resolution (the parts with the most edge cases).
- **Link checker over the built output:** every internal `href`/`src` must resolve to a file in `dist/` under the base path. This catches base-path bugs, which are the usual cause of "works locally, broken on Pages".
- **One end-to-end test** that runs the CLI binary on the fixture and serves `dist/` under `/repo/`.

## Risks

- **Base-path bugs** on project pages. The fix is the single URL builder plus the output link checker.
- **Leaking private notes.** The fix is draft/ignore defaults, a summary printed after every build ("published 132 notes, skipped 7 drafts"), and a `--dry-run`.
- **Scope creep toward a full static-site generator.** If you need much more than the Later list below, use Quartz, MkDocs, or Eleventy with a Markdown setup instead. It's worth checking whether one of them already fits before building this.

## Later (not v1)

Client-side search (e.g. Pagefind), tag pages, backlinks, RSS, KaTeX/mermaid, incremental builds, multiple themes.

## Process log

1. Checked that the output directory `<repo>\research\extraction\traces\` exists (`ls`; empty).
2. Wrote this file. No repository files were read for this task (it is a greenfield request).
