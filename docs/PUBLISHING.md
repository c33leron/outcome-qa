# Publishing a release

The GitHub repository is the primary distribution: the root exposes seven portable skills to the Skills CLI. The same checkout can generate a clean full-plugin marketplace. Tests, labs and CI stay in the repository, not in either installed payload. Offline archives are optional release assets.

## Release identity

- Package: `outcome-qa`
- Version: `0.1.1`
- Local release marketplace: `outcome-qa-releases`
- Install asset: `outcome-qa-0.1.1.zip`
- Source asset: `outcome-qa-source-0.1.1.zip`

A prepared directory or archive is not a publication receipt. Creating a remote repository, pushing, tagging and uploading release assets are deliberate publication steps. After the first authorized push, run the README command against the actual repository from a clean project before announcing the release.

## 1. Freeze the source

Check the latest published GitHub release and tags before choosing the version. Public versioning follows that release history, not a higher label used by a private/local plugin cache. Keep historical verification receipts under their actual tested identity; explicitly state when identical method content is carried into a differently numbered public release.

Confirm the intended repository, branch, working-tree changes, version and attribution. Record the source commit when one exists. Review source inventory changes; exclude private research, raw chat histories, credentials, generated caches and machine-specific paths. Keep tests, CI, synthetic examples and their provenance.

All public descriptions should say what the product does. Compatibility and verification claims must match the actual release evidence—not the presence of a manifest or a successful static check. Avoid stale alpha/beta labels and unsupported “works everywhere” claims.

## 2. Run the quality gates

From the source checkout, using Python 3.10+ (`py -3` on Windows):

```sh
python3 scripts/sync_shared.py
python3 scripts/validate_package.py
python3 -m unittest discover -s tests -v
```

Run the release-specific checks recorded in [Verification](VERIFICATION.md), including artifact membership, fresh extraction, install/list/remove lifecycle, update behavior and representative task discovery/execution. Keep infrastructure or authentication failures separate from product outcomes. CI and local checks are complementary; record the actual OS and host versions exercised.

## 3. Build a clean marketplace or optional offline assets

Build the normal full-plugin installation source with `python3 scripts/build_release.py --output-dir ../outcome-qa-marketplace`. For optional offline ZIPs, use new paths **outside the source tree**; builders refuse to overwrite.

```sh
python3 scripts/build_release.py --output /path/to/release/outcome-qa-0.1.1.zip
python3 scripts/package.py --output /path/to/release/outcome-qa-source-0.1.1.zip
```

`build_release.py --output-dir /path/to/new-bundle-directory` produces an unpacked bundle for inspection. `build_runtime.py` builds only the inner runtime; that is not the complete public marketplace bundle.

Expected install archive layout:

```text
outcome-qa-0.1.1/
├── README.md
├── MANIFEST.json
├── .agents/plugins/marketplace.json
├── .claude-plugin/marketplace.json
└── outcome-qa/
    ├── README.md
    ├── plugin.json
    ├── .codex-plugin/
    ├── .claude-plugin/
    ├── skills/
    ├── scripts/
    └── ...runtime references, adapters, schemas and licenses
```

The outer README comes from `distribution/INSTALL.md`; the inner README comes from `distribution/README.md`. Verify local links and command working directories in the **extracted artifact**, not only the source tree. Confirm that tests, labs, evals, example evidence and contributor-only scripts are absent from the install bundle.

## 4. Check the user journey

Follow [the installation guide](INSTALL.md) from a fresh project, including paths with spaces where supported. Use a local source path before publication; verify GitHub resolution afterward. If distributing the offline archive, also verify a fresh extraction. Verify registration and discovery, give the host a representative QA task, then test removal without harming unrelated plugins, skills or instructions.

Optional reviewer and standalone installations are separate paths: check their explicit preview/apply behavior and document their separate removal. Do not treat successful plugin uninstall as proof that these optional files disappeared.

Publish checksums alongside the artifacts. Re-download the published install asset and verify its checksum and contents before announcing completion. Retain the commands, exact versions and sanitized results behind the summary.

## 5. Publish a focused page

The public README should lead with the outcome, a short installation path, recognizable tasks and a concrete example. Link detailed compatibility, verification, support and security material instead of putting an internal development diary on the landing page.

Use only synthetic or explicitly authorized media and examples. Preserve [attribution](../THIRD_PARTY_NOTICES.md), [security reporting](../SECURITY.md) and [feedback guidance](../SUPPORT.md). A clean screenshot illustrates a captured state; it does not replace the underlying check.

After the explicit publication action, record the actual repository URL, tag, release assets and source revision. Announce what shipped and how to use it—not an unmeasured guarantee that it outperforms every alternative.
