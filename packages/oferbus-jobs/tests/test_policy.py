from oferbus_jobs import retry_delay_seconds


def test_retry_backoff_is_bounded_and_exponential() -> None:
    assert retry_delay_seconds(0) == 5
    assert retry_delay_seconds(1) == 5
    assert retry_delay_seconds(2) == 10
    assert retry_delay_seconds(3) == 20
    assert retry_delay_seconds(7) == 300
    assert retry_delay_seconds(20) == 300
