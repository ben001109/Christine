from christine.modelization.corpus import should_include_in_model_corpus


def test_model_corpus_excludes_runtime_and_generated_data():
    assert should_include_in_model_corpus("christine_final.py")
    assert should_include_in_model_corpus("docs/plans/x.md")
    assert not should_include_in_model_corpus("data/private_memory.json")
    assert not should_include_in_model_corpus("brain/generated/area_000001.py")
    assert not should_include_in_model_corpus(".env")
