from backend.main import build_prompt, normalize_generated_answer


def test_build_prompt_includes_fact_checking_and_concise_answer_guidance():
    prompt = build_prompt(
        'What is Databricks?',
        [{'title': 'Databricks overview', 'source': 'https://example.com', 'snippet': 'Databricks is a cloud data and AI platform.'}],
        [],
    )

    assert 'Databricks Learning Assistant' in prompt
    assert 'Never confuse Databricks' in prompt
    assert 'For simple questions' in prompt
    assert 'Delta Lake' in prompt
    assert 'Auto Loader' in prompt


def test_normalize_generated_answer_corrects_databricks_definition():
    bad_answer = 'Auto Loader is a Databricks feature for incremental file ingestion. It is a cloud-based data and AI platform built around Spark.'
    fixed = normalize_generated_answer('What is Databricks?', bad_answer)

    assert 'Databricks is a cloud-based data and AI platform' in fixed
    assert 'Auto Loader' not in fixed
