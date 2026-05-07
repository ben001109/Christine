from christine.modelization import ModelProviderRequest, ModelProviderResponse, NoopModelProvider


def test_noop_model_provider_is_explicitly_unavailable():
    provider = NoopModelProvider(reason="training disabled")
    response = provider.generate(ModelProviderRequest(prompt="hi"))

    assert response.available is False
    assert response.text == ""
    assert response.reason == "training disabled"


def test_model_provider_request_preserves_prompt_and_metadata():
    request = ModelProviderRequest(prompt="hello", system="sys", metadata={"target": "direct"})

    assert request.prompt == "hello"
    assert request.system == "sys"
    assert request.metadata == {"target": "direct"}
