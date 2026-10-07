#!/usr/bin/env python
"""Run the whole research pipeline, stage by stage, with validation.

    uv run python run_pipeline.py                  # everything
    uv run python run_pipeline.py --preflight-only # just check .env, tokens, tools
    uv run python run_pipeline.py --stages 01-03   # a range
    uv run python run_pipeline.py --from 02        # resume from a stage
    uv run python run_pipeline.py --only 03        # a single stage
    uv run python run_pipeline.py --force          # ignore completed-stage state
    uv run python run_pipeline.py --record-reference  # maintainers: pin outputs as the reference run

Before anything runs, preflight checks .env, the Hugging Face token, access to
every gated/pinned repo, required tools, GPU and disk. After each stage, the
stage's outputs are verified against their sha256 manifests; a stage is only
marked done when that passes. Completed stages are skipped on re-runs unless
their config or inputs changed.

Reproducibility: the sha256 of every deterministic output is compared with the
maintainers' reference run (config/reference_outputs.json). A mismatch means
you did not reproduce the published data byte-for-byte and stops the run
(override with --allow-reference-diff). A summary of every stage, its checks
and its reports is printed at the end and saved as logs/<run>/summary.md.
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

from lidpipe import config, paths, preflight
from lidpipe.manifest import read_manifest, sha256_file, verify_manifest
from lidpipe.stages import STAGES, select


def _manifest_hashes(dirs):
    return {str(d.relative_to(paths.ROOT)): sha256_file(d / 'manifest.json')
            for d in dirs if (d / 'manifest.json').exists()}


def _state_file(stage):
    return paths.STATE_DIR / f'{stage.id}_{stage.name}.json'


def is_current(stage):
    """True if the stage completed with this config and these inputs, and its outputs are intact."""
    f = _state_file(stage)
    if not f.exists():
        return False
    state = json.loads(f.read_text())
    if state.get('config_sha256') != stage.config_hash():
        return False
    if state.get('inputs') != _manifest_hashes(stage.inputs):
        return False
    return all(not verify_manifest(d) for d in stage.outputs)


def run_stage(stage, log_dir):
    for d in stage.inputs:
        problems = verify_manifest(d)
        if problems:
            producer = next((s for s in STAGES if d in s.outputs), None)
            fix = f'run_pipeline.py --only {producer.id} --force' if producer else 'the producing stage'
            raise SystemExit(f'stage {stage.id} inputs are not valid:\n  ' + '\n  '.join(problems)
                             + f'\nRegenerate them with: {fix}')
    env = {**os.environ, 'PYTHONPATH': str(paths.ROOT) + os.pathsep + os.environ.get('PYTHONPATH', ''),
           'PYTHONUNBUFFERED': '1', 'HF_HUB_DISABLE_PROGRESS_BARS': '1'}
    log_path = log_dir / f'{stage.id}_{stage.name}.log'
    with open(log_path, 'a', encoding='utf-8') as log:
        for step in stage.steps:
            print(f'  -> {step}')
            log.write(f'\n===== {step} =====\n')
            log.flush()
            proc = subprocess.Popen([sys.executable, str(paths.SCRIPTS / step)], cwd=paths.ROOT, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                print('     ' + line, end='')
                log.write(line)
            if proc.wait():
                raise SystemExit(f'stage {stage.id} failed in {step} (exit {proc.returncode}); log: {log_path}')
    problems = [p for d in stage.outputs for p in verify_manifest(d)]
    if problems:
        raise SystemExit(f'stage {stage.id} output validation failed:\n  ' + '\n  '.join(problems))
    paths.STATE_DIR.mkdir(exist_ok=True)
    _state_file(stage).write_text(json.dumps({
        'stage': stage.id, 'completed_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'config_sha256': stage.config_hash(), 'inputs': _manifest_hashes(stage.inputs),
        'outputs': _manifest_hashes(stage.outputs)}, indent=2))


def _load_reference():
    if paths.REFERENCE_OUTPUTS.exists():
        return json.loads(paths.REFERENCE_OUTPUTS.read_text(encoding='utf-8'))
    return {}


def reference_check(stage):
    """Compare this stage's output files with the reference run.
    Returns (status, details): status is MATCH, DIFF, NO-REFERENCE or SKIPPED."""
    if not stage.deterministic:
        return 'SKIPPED', ['outputs are not expected to be bit-identical (e.g. GPU training)']
    ref = _load_reference()
    details, status = [], 'MATCH'
    for d in stage.outputs:
        key = str(d.relative_to(paths.ROOT))
        if key not in ref:
            return 'NO-REFERENCE', [f'{key}: no reference recorded']
        mine = {f: e['sha256'] for f, e in read_manifest(d)['files'].items()}
        for f, sha in ref[key].items():
            if mine.get(f) != sha:
                status = 'DIFF'
                details.append(f'{key}/{f}: differs from reference')
    return status, details or ['all output files byte-identical to the reference run']


def record_reference(stages):
    ref = _load_reference()
    for s in stages:
        if s.deterministic:
            for d in s.outputs:
                ref[str(d.relative_to(paths.ROOT))] = {f: e['sha256'] for f, e in read_manifest(d)['files'].items()}
    paths.REFERENCE_OUTPUTS.write_text(json.dumps(ref, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(f'recorded reference hashes for {len(ref)} output directories in {paths.REFERENCE_OUTPUTS.name}')


def write_summary(log_dir, rows, preflight_report, outcome):
    lines = ['# Pipeline run summary', '', f'Outcome: **{outcome}**', '',
             '| stage | status | time | reference check |', '|---|---|---:|---|']
    lines += [f'| {r["stage"]} | {r["status"]} | {r["seconds"]} | {r["reference"]} |' for r in rows]
    for r in rows:
        if r['details'] or r['reports']:
            lines += ['', f'## {r["stage"]}', '']
            lines += [f'- {d}' for d in r['details']]
            lines += [f'- report: `{p}`' for p in r['reports']]
    lines += ['', '## Preflight', '', '```', preflight_report, '```']
    text = '\n'.join(lines) + '\n'
    (log_dir / 'summary.md').write_text(text, encoding='utf-8')
    print('\n' + '=' * 70 + '\n' + text.split('\n## Preflight')[0] + '\n' + '=' * 70)
    print(f'Summary saved to {(log_dir / "summary.md").relative_to(paths.ROOT)}; '
          f'stage logs in {log_dir.relative_to(paths.ROOT)}/')


def run_metadata(log_dir, stages):
    def sh(*cmd):
        try:
            return subprocess.run(cmd, cwd=paths.ROOT, capture_output=True, text=True, check=True).stdout.strip()
        except Exception:  # noqa: BLE001
            return None
    meta = {'started_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'git_commit': sh('git', 'rev-parse', 'HEAD'),
            'git_dirty': bool(sh('git', 'status', '--porcelain')),
            'python': sys.version, 'platform': platform.platform(),
            'config_sha256': config.config_hash(), 'stages': [s.id for s in stages],
            'packages': (sh('uv', 'pip', 'freeze') or '').splitlines()}
    (log_dir / 'run_metadata.json').write_text(json.dumps(meta, indent=2))


def main():
    sys.stdout.reconfigure(line_buffering=True)  # live output even when piped to a file/tee
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stages', help='range like 01-03 (execution order: 01 02 05 03 00 04 06 07)')
    ap.add_argument('--from', dest='start', help='start at this stage')
    ap.add_argument('--only', help='comma-separated stage ids')
    ap.add_argument('--force', action='store_true', help='re-run stages even if already complete')
    ap.add_argument('--preflight-only', action='store_true')
    ap.add_argument('--dry-run', action='store_true', help='show what would run')
    ap.add_argument('--allow-reference-diff', action='store_true',
                    help='continue when outputs differ from the reference run (results then are not comparable)')
    ap.add_argument('--record-reference', action='store_true',
                    help='maintainers: store the current outputs as the reference run')
    args = ap.parse_args()

    stages = select(args.stages, args.start, args.only)
    pending = [s for s in stages if not s.implemented]
    stages = [s for s in stages if s.implemented]
    for s in pending:
        print(f'note: stage {s.id} ({s.name}) is not implemented yet; skipping')

    print('Preflight checks')
    result = preflight.run(stages)
    print(result.report())
    if result.failed:
        raise SystemExit('\nPreflight failed. Fix the items marked FAIL and re-run.')
    if args.preflight_only:
        return

    run_id = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_dir = paths.LOGS_DIR / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    run_metadata(log_dir, stages)

    rows, outcome = [], 'FAILED'
    try:
        for s in stages:
            row = {'stage': f'{s.id} {s.name}', 'status': 'up to date (skipped)', 'seconds': 0,
                   'reference': '', 'details': [], 'reports': []}
            rows.append(row)
            if args.dry_run:
                print(f'\n[{s.id}] {s.name} (dry run)')
                for step in s.steps:
                    print(f'  -> {step}')
                row['status'] = 'dry run'
                continue
            if not args.force and is_current(s):
                print(f'\n[{s.id}] {s.name}: up to date, skipping')
            else:
                print(f'\n[{s.id}] {s.name}')
                row['status'] = 'running'
                t = time.time()
                try:
                    run_stage(s, log_dir)
                except SystemExit as e:
                    row['status'], row['details'] = 'FAILED', [str(e)]
                    raise
                row['status'], row['seconds'] = 'ran, outputs verified', round(time.time() - t)
                print(f'[{s.id}] done in {row["seconds"]}s')
            row['reports'] = [str(p.relative_to(paths.ROOT)) for p in s.reports if p.exists()]
            status, details = reference_check(s)
            row['reference'], row['details'] = status, details
            print(f'[{s.id}] reference check: {status}' + ''.join(f'\n     {d}' for d in details))
            if status == 'DIFF' and not args.allow_reference_diff and not args.record_reference:
                raise SystemExit(f'stage {s.id} outputs differ from the reference run (see above). Your data is '
                                 f'not byte-identical to the published run, so results are not comparable. '
                                 f'Check config/locks.json and package versions, or pass --allow-reference-diff.')
        if args.record_reference and not args.dry_run:
            record_reference(stages)
        outcome = 'SUCCESS'
    finally:
        if not args.dry_run:
            write_summary(log_dir, rows, result.report(), outcome)


if __name__ == '__main__':
    main()
