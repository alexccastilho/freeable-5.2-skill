# Plan: Markdown notes folder to a GitHub Pages site

One thing to decide before any code is written: existing tools already do this (MkDocs, Quartz, Eleventy, Hugo). If you just want your notes online, MkDocs with a theme gets you there in an afternoon with no code to maintain. I have planned a small custom tool below because that is what you asked for, and it is a reasonable choice if you want full control over the output or a tool with no configuration. If the goal is only the result, say so and I will plan the MkDocs route instead.

## Questions I would ask

1. **Custom tool, or a thin setup around an existing generator?** Default: custom tool, as requested.
2. **What do the notes look like?** Plain Markdown, or Obsidian-style (`[[wikilinks]]`, `![[embeds]]`, callouts)? Default: plain CommonMark plus GitHub-style tables and fenced code, with `[[wikilinks]]` supported because they are common in note folders. Embeds and callouts are left out of version 1.
3. **Are all notes meant to be public?** A Pages site is readable by anyone on the internet, in most plans even when the repository is private. Default: every note is published unless its front matter says `draft: true` or `publish: false`, and the tool also accepts an ignore list.
4. **Language.** Default: Python 3.11+, installed with `pipx`. If you would rather have a single binary or an `npx` command, the design is the same and only the libraries change.
5. **Where will the site live?** `username.github.io` (served at `/`) or a project repository (served at `/<repo>/`)? Default: project repository, so the tool must handle a base path.
6. **Do you need search, tags, or backlinks?** Default: none in version 1. Navigation is a folder tree plus an index page.
7. **How large is the folder?** Default: under a few thousand notes, so a full rebuild each time is fine and no incremental build is needed.

## What the tool does

Working name `notesite`.

```
notesite build <notes-dir> --out _site --base-url /my-repo/
notesite serve <notes-dir>          # local preview with rebuild on change
notesite init-pages                 # writes the GitHub Actions workflow
```

`build` is the whole product. `serve` and `init-pages` are conveniences that reuse it.

### Build pipeline

1. **Discover.** Walk the folder, collect `.md` files and non-Markdown files (images, PDFs). Skip dotfiles, the output folder, anything matched by the ignore list, and notes marked as drafts.
2. **Parse.** Read optional YAML front matter (`title`, `date`, `draft`). The title falls back to the first `# heading`, then to the file name.
3. **Map paths.** `notes/projects/Idea One.md` becomes `projects/idea-one/index.html`, which gives clean URLs. The map from source path to output URL is built for every note before anything is rendered, because link rewriting depends on it.
4. **Render.** Markdown to HTML with a CommonMark parser (`markdown-it-py`), with tables, fenced code, and heading anchors enabled.
5. **Rewrite links.** This is the part that decides whether the site works:
   - relative links to `other.md` or `other.md#section` become the mapped URL;
   - `[[Note Name]]` and `[[Note Name|label]]` resolve by title or file name, case-insensitively;
   - image and attachment paths are rewritten to the copied asset location;
   - every internal URL is prefixed with the base URL;
   - a link whose target does not exist is reported as a warning, and `--strict` turns warnings into a failed build.
6. **Template.** One Jinja2 layout: page title, sidebar built from the folder tree, content, and a footer. One bundled stylesheet with light and dark modes. No JavaScript in version 1.
7. **Write.** Emit the HTML, copy assets, generate `index.html` (uses `index.md` or `README.md` from the root if present, otherwise a generated list of notes), `404.html`, and an empty `.nojekyll` file.

### GitHub Pages specifics

- **Base path.** A project site is served under `/<repo>/`, so root-relative links such as `/css/site.css` break. Every generated URL goes through one function that applies `--base-url`. The workflow passes the repository name automatically.
- **Jekyll.** Pages runs Jekyll on branch-published content by default, and Jekyll drops files and folders that start with an underscore. The `.nojekyll` file disables that.
- **Deployment.** Default is a GitHub Actions workflow that runs `notesite build` on every push to the main branch and publishes the result with the official Pages actions. This keeps generated HTML out of the repository history. The alternative, pushing output to a `gh-pages` branch, is simpler to understand but mixes build output into git; I would offer it only if you prefer it.
- **To verify at implementation time:** the current major versions of the Pages actions (`actions/configure-pages`, `actions/upload-pages-artifact`, `actions/deploy-pages`) and the permissions block they require. I am not pinning these from memory.

## Build order

Each step ends with something you can run.

1. **Skeleton and happy path.** CLI entry point, discovery, rendering, one template, output written. Checked by building a fixture folder of five notes and opening the result in a browser.
2. **Links and assets.** The path map, link rewriting, wikilinks, asset copying, broken-link warnings. This is where most of the bugs will be, so it gets the most tests: a fixture folder with nested folders, spaces and accents in file names, anchors, a missing target, and two notes with the same name in different folders.
3. **Base URL.** Build the fixture with `--base-url /repo/` and serve it locally under that prefix to confirm that no link escapes it.
4. **Drafts and ignore rules.** Tested by asserting that an excluded note produces no file and that no other page links to it.
5. **Navigation and index.** Sidebar tree, generated index, 404 page.
6. **`init-pages` and a real deployment.** Push a sample repository and confirm the published site loads, including a nested page and an image, at the project URL.
7. **`serve`.** Local preview with rebuild on file change.
8. **Packaging.** `pyproject.toml` with a console script, a README with a three-command quick start.

Steps 1 to 6 are the usable product. Steps 7 and 8 can follow.

## Decisions I have made, and why

- **Full rebuild every time.** Incremental builds add cache invalidation problems that a notes folder of this size does not justify.
- **Clean URLs through `folder/index.html`.** Works on Pages with no server configuration.
- **Duplicate note names.** A wikilink that matches two notes resolves to the one closest to the linking note's folder, and the build prints a warning. Silent guessing here would produce links that go to the wrong page.
- **Raw HTML in notes is passed through.** These are your own notes, so sanitising would only get in the way. This would change if the tool ever built content from other people.
- **No theme system.** One layout and one stylesheet, both overridable by placing files in a `_theme/` folder. A plugin system is out of scope.

## Out of scope for version 1

Full-text search, tag pages, backlinks, a graph view, RSS, Obsidian embeds and callouts, math rendering, and custom domains (a `CNAME` file can be added by hand in the notes folder and will be copied as an asset). Each can be added later without changing the pipeline above.

## Risks

- **Publishing something private.** The largest real risk. Mitigations: the draft flag, the ignore list, and a `--dry-run` that lists exactly which files would be published. I would run the dry run before the first deployment.
- **Link edge cases.** Note folders accumulate odd file names. The fixture in step 2 covers the cases I know of, and `--strict` in CI catches regressions.
- **Pages behaviour changing.** The deployment workflow is the only part tied to GitHub, and it is about twenty lines.

## Process log

1. Ran one shell command in the shopmini fixture: `find` to list files, `wc -c` for file sizes, and `ls` of the traces output folder. This was a single exploration pass done before starting any of the four tasks.
2. Ran one shell command in the shopmini fixture: `cat -n` over `package.json`, `README.md`, `src/server.js`, `src/db.js`, `src/clock.js`, `src/admin/bulkImport.js`, `src/notifications/mailer.js`, `src/orders/orderService.js`, `src/users/userService.js`, `test/orders.test.js`; then `ls -la` of the fixture root and `ls` of the traces output folder. None of this was used for this task.
3. Called the advisor tool once.
4. Wrote this file with the Write tool.
