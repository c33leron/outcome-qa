# Bounded behavioral development evaluations

This offline Python 3.10+ helper prepares task-only packets and checks **external,
independently supplied adjudications** against frozen inputs and raw artifacts.
It does not call a model, collect telemetry, or decide semantic truth with regexes.
The sixteen synthetic cases cover decision, actor, discovery, durable-outcome,
cleanup, continuation, and requirements-review failures. The requirements cases
exercise missing artifact placement, conflicting and superseded sources, a change
after earlier acceptance, a smoke with no specification, linked local requirements,
an owner question ready to forward, and delivery through a local mock. Healthy
and non-QA controls cover a clear requirement and a simple translation. These
public **development cases** have
visible rubrics. Disclose when a performer has seen the source or rubric before a
run. Unit tests establish the helper's boundary behavior. Model behavior requires
recorded runs and independent review.

## 1. Freeze the experiment before dispatch

Use a new directory outside the checkout. Create an arms JSON array with exactly
`id`, `source_sha256`, and `description` per arm. IDs are unique safe filename
slugs; `source_sha256` pins the complete source/runtime snapshot you actually retain, including supporting references. An entrypoint-only hash misses changes in those references.
For example, generate the identity from real bytes, not a made-up version label:

```sh
python3 - /absolute/prior-runtime.zip /absolute/candidate-runtime.zip > /absolute/run/arms.json <<'PY'
import hashlib, json, pathlib, sys
print(json.dumps([
    {"id": name, "source_sha256": hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest(),
     "description": "Explicit " + name + " runtime snapshot; record host/model/config separately"}
    for name, path in zip(("prior", "candidate"), sys.argv[1:])
]))
PY
python3 scripts/behavioral_eval.py prepare evals/behavior-cases.json \
  --arms /absolute/run/arms.json --repeats 1 --out /absolute/run/frozen
```

The output supplies `manifest_sha256` and the number of planned trials. A
canonical frozen source with reviewer expectations is saved as `source.json`;
`packets/p000001.json` and subsequent sequential filenames contain **only**
`id` and `prompt`. Filenames are independent of logical case IDs, so `Case` and
`case` remain distinct on case-insensitive filesystems. Packet SHA-256 values
cover its exact bytes, including any evidence embedded in the prompt.
The manifest pins arms, source, packets and every case × arm × repeat slot.
Preparation refuses to overwrite an existing directory. It writes a private
sibling staging directory before reserving the output; a staging-write failure
leaves the final output available for retry. Publication uses exclusive creation
and hard links on the same filesystem. Failure cleanup removes only recorded,
unchanged files and empty owned directories, never recursively deletes additions.
A changed file or interrupted partial write may leave a `.NAME.prepare-*` staging
directory for inspection; do not blindly delete it.

Give each performer its packet, the intended arm setup, and any case fixture
described below. Keep the source, reviewer expectations and reviews out of the
performer's workspace. Keep unrelated history and candidate
identity out where feasible; record unavoidable contamination. Use the same
input bytes for matched arms. An explicit prior-skill trial is not a
skill-disabled baseline. Record actual host/model/configuration and any
uncontrolled differences in trial notes and raw trace; do not infer uplift from
labels. Arm hashes pin declared source, not what the agent actually loaded.

### Local fixtures for c15 and c16

For each trial of c15 or c16, create a fresh working directory and copy the
contents of `evals/behavior-fixtures/<case-id>/` into its `fixture/` directory.
Run the performer from that working directory. Keep a retained snapshot and
record SHA-256 hashes of the fixture files by relative path in the trial notes.
Use identical fixture bytes across arms and repeats. The helper hashes the packet
but does not copy, hash or mount these companion files.

For c15, the fixtures are read-only. For c16, allow only the mock's local receipt
write beside `fixture/` and use a fresh directory without an existing receipt.
Keep real messaging connectors unavailable. Preserve the command trace and any
`qa-desk-receipt.json` as raw evidence. The mock receipt confirms only a local
outbox write and contains no stakeholder reply. The c14 draft exercise needs no
fixture or write access.

Register all planned attempts **before** dispatch. A failed provider/setup call,
timeout or malformed run retains its slot; never overwrite it with a successful
retry. `--repeats` creates separate slots, not a best-of-N selector. For a new
unplanned retry, freeze a new supplemental experiment and report it alongside,
not instead of, the original. The helper cannot discover hidden/unregistered
runs; honest launch capture remains an operator responsibility.

## 2. Preserve raw records and obtain independent review

Each planned slot must appear exactly once in both input documents, including
failed and not-run attempts. Both document envelopes have integer `version: 1`,
the preparation's `manifest_sha256`, and either `trials` or `reviews` arrays.
A trial uses exactly these fields:

```json
{
  "trial_id": "t000001",
  "case_id": "c01",
  "arm_id": "prior",
  "input_sha256": "COPY THE PACKET SHA-256 FROM ITS PLANNED SLOT",
  "status": "completed",
  "performer_id": "performer-a",
  "notes": "Describe actual host/model/config and any limitations or setup errors.",
  "artifacts": [
    {"id": "transcript", "path": "raw/t000001-answer.txt", "sha256": "HASH OF RAW FILE BYTES"},
    {"id": "tool_trace", "path": "raw/t000001-tools.txt", "sha256": "HASH OF RAW FILE BYTES"}
  ]
}
```

Values in capitals above are field explanations, not executable digests. Use the
manifest's actual planned identity/input values and hash the saved raw bytes.
`status` is `completed`, `provider_error`, `timeout`, `invalid`, or `not_run`.
Every attempted run needs a nonempty UTF-8 `transcript` (the raw error record for
an unsuccessful attempt). A not-run slot needs an honest reason in `notes` and
may have an empty artifact array. Save any available tool trace even on failure.
Do not rewrite an error into a clean answer. Artifact paths are relative to
`--artifact-root`; parent/absolute paths, symlink traversal and nonfiles fail.
Validation reads and hashes the bytes from one safely opened regular-file handle,
not a second pathname open after hashing. POSIX traversal uses anchored no-follow,
nonblocking opens; the fallback also checks opened identity and path components.

An independent human or separately assigned reviewer inspects the task, hidden
rubric, raw answer and native tool trace. Reviewer judgments are **trusted
inputs**, not an automatic semantic oracle; authorship and reviewer competence
cannot be proven by this helper. Declared performer/reviewer IDs must differ.
Prefer blind identity and a second review for disputed judgments. A review uses
exactly these fields:

```json
{
  "trial_id": "t000001",
  "trial_sha256": "CANONICAL SHA-256 OF THE WHOLE TRIAL OBJECT",
  "reviewer_id": "reviewer-b",
  "outcome": {
    "pass": true,
    "reason": "Explain why the answer reaches the supported conclusion.",
    "evidence": [{"artifact_id": "transcript", "line_start": 1, "line_end": 1,
                  "quote": "Exact first line from this raw artifact."}]
  },
  "adherence": {
    "pass": true,
    "reason": "Explain compliance with scope, actor, permitted actions and output contract.",
    "evidence": [{"artifact_id": "transcript", "line_start": 1, "line_end": 1,
                  "quote": "Exact first line from this raw artifact."}]
  },
  "observed_method": {
    "loaded": null,
    "reason": "Tool trace unavailable or insufficient to establish applicable reads.",
    "evidence": []
  }
}
```

`pass`/`loaded` accept JSON `true`, `false`, or `null`, never strings or numbers.
For outcome/adherence, any non-null judgment needs exact transcript evidence.
For observed loading, any non-null judgment needs exact **tool_trace** evidence;
a method name in the answer is not a read. The reviewer must inspect the actual
successful entrypoint and applicable reference reads, including truncated-output
recovery, rather than award loading for an announcement or failed open. A
complete trace showing no method read supports `loaded: false`; missing trace or
ambiguous/partial evidence should be `null`, not fabricated absence. For the
non-QA neighbor, not loading a QA method is healthy.

Evidence uses one-based inclusive lines; `quote` must equal the selected lines
joined by `\n` (without a trailing newline). This establishes reference integrity,
**not whether the quote supports the judgment**. A dishonest or mistaken reviewer
can still misjudge a real quote. Outcome/adherence for noncompleted runs must be
`null`; their provider/setup failures are not agent-quality failures. A method
read before a later provider failure may still be recorded independently.

The canonical object hash is deliberately different from a raw file hash:

```python
import hashlib, json
trial_sha256 = hashlib.sha256(json.dumps(
    trial, ensure_ascii=False, sort_keys=True,
    separators=(',', ':'), allow_nan=False
).encode('utf-8')).hexdigest()
```

Changing the trial's arm, input, status or raw-artifact descriptors invalidates
an old review. Raw artifact tampering invalidates its declared hash. The same
canonical rule computes `manifest_sha256`. Duplicate JSON keys are rejected.

## 3. Score without collapsing dimensions

```sh
python3 scripts/behavioral_eval.py score /absolute/run/frozen/manifest.json \
  --trials /absolute/run/trials.json --reviews /absolute/run/reviews.json \
  --artifact-root /absolute/run > /absolute/run/score.json
```

The read-only scorer returns per-trial observations and three separate counters:

- **Outcome:** evidence-bounded correctness, including a justified no-bug verdict.
- **Adherence:** requested actor/scope, authorized actions and delivery contract.
- **Observed method loading:** loaded, not loaded or unmeasured. It is not an
  outcome score and never turns a correct inline answer into a product failure.

`valid` means the supplied records pass structure/binding/reference checks.
`experiment` is `COMPLETE`, `INCOMPLETE`, or `INVALID`; unmeasured loading still
leaves measurement incomplete even if semantic quality is clean. `quality`
reflects only outcome/adherence. Thus a correct inline result with missing trace
can have `quality: PASS`, `experiment: INCOMPLETE`, and aggregate
`verdict: INCOMPLETE`. Observed `loaded: false` is not itself a failure.

Aggregate exit codes: **0 PASS**, **1 FAIL**, **2 INCOMPLETE/FAIL_WITH_GAPS**,
**3 INVALID**. Known false judgments are retained when another dimension is
unknown. Missing/duplicate IDs, omitted repeats, empty reviews, unsupported
positive judgments, malformed types and changed artifacts cannot produce PASS.
An invalid report's partial counters must not be used as a score. Report all
attempts and configuration limitations; do not cherry-pick successful repeats
or interpret a passing prior arm as an improvement.

The existing outcome helper v1 is unchanged. To include this experiment in a
normal QA report, attach `manifest.json`, `score.json`, trial/review documents and
raw trace as ordinary `{id,path,sha256}` artifacts. A structurally valid report
still does not independently prove the adjudication or product outcome.

## Local verification

```sh
python3 -m unittest discover -s tests -p test_behavioral_eval.py -v
```

These controls exercise real CLI preparation/scoring, healthy results, strict
coverage, input/artifact/reviewer binding, failed attempts, missing traces,
false PASS boundaries and safe path handling. The broader suite/package gates
remain separate. Scripts, source fixtures and these docs are development
material; they do not add a runtime hook, mandatory workflow or evidence schema.
