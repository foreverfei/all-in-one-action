import numpy as np

from lineA.executors.base import MockExecutor


def test_ordered_rollout_is_nested_executor_call() -> None:
    image = np.linspace(0.0, 1.0, 12 * 12 * 3, dtype=np.float32).reshape(12, 12, 3)
    executor = MockExecutor()

    saved = executor.restore(executor.restore(image, "dehaze"), "derain")
    expected = executor.restore(executor.restore(image, "dehaze"), "derain")
    reverse = executor.restore(executor.restore(image, "derain"), "dehaze")

    assert np.array_equal(saved, expected)
    assert saved.shape == reverse.shape
