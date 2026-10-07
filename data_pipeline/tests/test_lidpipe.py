import json
import unicodedata

import numpy as np
import pytest
from sklearn.metrics import f1_score

from lidpipe import paths
from lidpipe.labels import SCORED, canonical_prediction, gold_language
from lidpipe.metrics import per_label, summarise
from lidpipe.stages import ORDER, select
from lidpipe.text import normalise, script_of


def test_normalise_keeps_indic_combining_marks():
    # The old OpenLID cleaner turned these into "ससकतम भष" / "ශර ලකව".
    assert normalise('संस्कृतम् भाषा') == 'संस्कृतम् भाषा'
    assert normalise('ශ්‍රී ලංකාව') == 'ශ්‍රී ලංකාව'  # ZWJ kept


def test_normalise_is_nfc_and_idempotent():
    decomposed = unicodedata.normalize('NFD', 'café  ශ්‍රී​﻿')
    out = normalise(decomposed)
    assert unicodedata.is_normalized('NFC', out)
    assert out == 'café ශ්‍රී'
    assert normalise(out) == out


def test_script_detection():
    assert script_of('ශ්‍රී ලංකාව') == 'Sinh'
    assert script_of('संस्कृतम्') == 'Deva'
    assert script_of('مرحبا') == 'Arab'
    assert script_of('12345 !!') == 'Zyyy'
    assert script_of('日本語のテキスト') == 'Jpan'


def test_arabic_policy():
    # Gold: only `arb` is MSA; `ara` is never merged in.
    assert gold_language('commonlid', 'ara') == 'ara'
    assert gold_language('wili_2018', 'ara') == 'ara'
    assert gold_language('commonlid', 'arb') == 'arb'
    # Predictions: LID-176's macro `ar` is credited as arb (documented limitation).
    assert canonical_prediction('__label__ar', 'مرحبا') == 'arb_Arab'
    assert canonical_prediction('__label__arb_Arab', 'مرحبا') == 'arb_Arab'


def test_prediction_script_comes_from_text_when_missing():
    assert canonical_prediction('__label__sa', 'संस्कृतम्') == 'san_Deva'
    assert canonical_prediction('__label__sa', 'සංස්කෘතම්') == 'san_Sinh'
    assert canonical_prediction('pi', 'ධම්ම') == 'pli_Sinh'
    assert canonical_prediction('__label__san_Deva', 'සංස්කෘතම්') == 'san_Deva'  # explicit script wins


def test_wili_als_override():
    assert gold_language('wili_2018', 'als') == 'gsw'


def test_scorer_matches_sklearn_and_ignores_absent_labels():
    gold = ['sin_Sinh', 'sin_Sinh', 'pli_Sinh', 'eng_Latn', 'eng_Latn', 'pli_Sinh']
    pred = ['sin_Sinh', 'pli_Sinh', 'pli_Sinh', 'eng_Latn', 'fra_Latn', 'xxx_Zyyy']
    t = per_label(gold, pred).set_index('label')
    present = ['sin_Sinh', 'pli_Sinh', 'eng_Latn']
    ref = f1_score(gold, pred, labels=present, average=None, zero_division=0)
    np.testing.assert_allclose(t.loc[present, 'f1'], ref)
    assert np.isnan(t.loc['san_Sinh', 'f1'])          # absent -> NaN, not 0
    assert t.loc['fra_Latn', 'fp'] == 1                # false positive still counted
    s = summarise(gold, pred, n_boot=0)
    assert s['macro_all'] == pytest.approx(ref.mean())
    assert s['outside_scored_predictions'] == 1


def test_bootstrap_is_deterministic():
    gold = ['sin_Sinh'] * 30 + ['pli_Sinh'] * 30
    pred = ['sin_Sinh'] * 25 + ['pli_Sinh'] * 35
    assert summarise(gold, pred, n_boot=200, seed=3) == summarise(gold, pred, n_boot=200, seed=3)


def test_stage_selection():
    assert [s.id for s in select('01-07')] == ORDER
    assert [s.id for s in select(only='03')] == ['03']
    with pytest.raises(SystemExit):
        select('07-01')
    with pytest.raises(SystemExit):
        select(only='99')


def _eval_rows(name):
    path = paths.benchmark_eval(name)
    if not path.exists():
        pytest.skip('run stage 02 first')
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f]


def test_flores_eval_is_script_qualified_and_has_native_sinhala():
    rows = _eval_rows('flores_plus')
    labels = {r['label'] for r in rows}
    assert {'sin_Sinh', 'san_Deva', 'arb_Arab'} <= labels
    assert all(r['label_raw'] == 'arb' and script_of(r['text']) == 'Arab' for r in rows if r['label'] == 'arb_Arab')
    assert sum(r['label'] == 'sin_Sinh' for r in rows) == 1012


def test_wili_is_test_split_only_without_arabic():
    rows = _eval_rows('wili_2018')
    assert all(r['sample_id'].startswith('wili_2018:test:') for r in rows)
    assert 'arb_Arab' not in {r['label'] for r in rows}
    assert sum(r['label'] == 'sin_Sinh' for r in rows) == 500


def test_benchmark_eval_text_is_nfc_and_scored():
    for name in paths.BENCHMARK_NAMES:
        rows = _eval_rows(name)
        assert all(unicodedata.is_normalized('NFC', r['text']) for r in rows)
        assert {r['label'] for r in rows} <= set(SCORED)


def test_segment_packs_sentences_within_limit():
    from lidpipe.text import segment
    text = 'එවං මෙ සුතං. ' * 40 + 'x' * 450
    units = segment(text.strip(), 200)
    assert all(len(u) <= 200 for u in units)
    assert ''.join(units).replace(' ', '') == text.strip().replace(' ', '')  # nothing lost
    assert segment('short text.', 200) == ['short text.']


def test_near_duplicates_are_verified_by_jaccard():
    from lidpipe.dedup import clusters, near_duplicate_pairs, near_matches
    a = 'අථ ඛො භගවා අම්බලට්ඨිකායං රාජාගාරකෙ එකරත්තිවාසං උපගච්ඡි'
    texts = [a, a + '.', 'සම්පූර්ණයෙන් වෙනස් වාක්‍යයක් මෙහි ඇත']
    pairs = near_duplicate_pairs(texts, threshold=0.8)
    assert pairs == [(0, 1)]
    assert clusters(3, pairs) == [0, 0, 2]
    assert near_matches([a + '!', texts[2]], [a]) == {0}


def _target(split):
    path = paths.TARGET / split / f'{split}.jsonl'
    if not path.exists():
        pytest.skip('run stage 01 first')
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f]


def test_target_release_is_leakage_free():
    splits = {s: _target(s) for s in ('train', 'validation', 'test')}
    blocks = {s: {r['block_id'] for r in rows} for s, rows in splits.items()}
    hashes = {s: {r['text_sha256'] for r in rows} for s, rows in splits.items()}
    for a, b in (('train', 'validation'), ('train', 'test'), ('validation', 'test')):
        assert not blocks[a] & blocks[b]
        assert not hashes[a] & hashes[b]
    for rows in splits.values():
        assert {r['label'] for r in rows} == {'sin_Sinh', 'pli_Sinh', 'san_Sinh'}
        assert all(len(r['text']) <= 200 and script_of(r['text']) == 'Sinh' for r in rows)


def test_hub_repo_comes_from_env(monkeypatch):
    from lidpipe import hub
    monkeypatch.setenv('HF_ORG', 'my-lab')
    monkeypatch.setenv('HF_TARGET_DATASET', 'my-copy')
    assert hub.target_dataset_repo() == 'my-lab/my-copy'
    lock = {'repo_id': '{HF_ORG}/{HF_TARGET_DATASET}', 'revision': 'abc', 'published_repo': 'script-langid/x'}
    # A re-hosted copy cannot use the original commit; sha256 pins verify it instead.
    assert hub.resolve(lock) == ('my-lab/my-copy', None)
    monkeypatch.setenv('HF_ORG', 'script-langid')
    monkeypatch.setenv('HF_TARGET_DATASET', 'x')
    assert hub.resolve(lock) == ('script-langid/x', 'abc')


def test_preflight_fails_without_token(monkeypatch):
    from lidpipe import preflight
    monkeypatch.setenv('HF_TOKEN', '')
    c = preflight.Check()
    preflight._hf(c, {})
    assert c.failed and 'HF_TOKEN' in c.report()


def test_preflight_rejects_invalid_token(monkeypatch):
    pytest.importorskip('huggingface_hub')
    from lidpipe import preflight
    monkeypatch.setenv('HF_TOKEN', 'hf_definitely_not_a_valid_token')
    c = preflight.Check()
    try:
        preflight._hf(c, {})
    except Exception:  # noqa: BLE001 - offline machines
        pytest.skip('no network')
    assert c.failed
    assert any(s == 'fail' and n == 'HF_TOKEN valid' for s, n, _ in c.results) or 'whoami' in c.report()


def test_preflight_unpublished_release_message(tmp_path):
    from lidpipe import preflight
    c = preflight.Check()
    preflight._local_release(c, 'target_dataset', {'path': str(tmp_path / 'nope'), 'files_sha256': {'a.jsonl': 'x'}})
    assert c.failed and 'resplit_target.py' in c.report()
