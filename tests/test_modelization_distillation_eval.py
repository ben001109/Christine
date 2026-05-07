from christine.modelization import DistillationEvalResult, assess_distillation_readiness


def test_distillation_eval_requires_all_thresholds():
    result = DistillationEvalResult(
        personality_score=0.92,
        routing_accuracy=0.88,
        safety_score=1.0,
        regression_passed=True,
    )

    readiness = assess_distillation_readiness(result)

    assert readiness.ready is True
    assert readiness.reason == "ready"


def test_distillation_eval_blocks_low_safety_even_when_personality_is_good():
    result = DistillationEvalResult(
        personality_score=0.95,
        routing_accuracy=0.95,
        safety_score=0.7,
        regression_passed=True,
    )

    readiness = assess_distillation_readiness(result)

    assert readiness.ready is False
    assert readiness.reason == "safety-below-threshold"


def test_distillation_eval_blocks_failed_regression_suite():
    result = DistillationEvalResult(1.0, 1.0, 1.0, regression_passed=False)

    readiness = assess_distillation_readiness(result)

    assert readiness.ready is False
    assert readiness.reason == "regression-failed"
