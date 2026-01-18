import requests
import dramatiq


@dramatiq.actor(store_results=True)
def do_something():
    res = requests.get('https://partyman.cloud')


@dramatiq.actor(
    max_retries=3,
    min_backoff=60_000,  # 60 seconds
    max_backoff=60_000,  # Fixed delay, not exponential
)
def post_with_retry(url, payload=None, headers=None):
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
    except requests.exceptions.RequestException as exc:
        raise dramatiq.errors.Retry(str(exc))

    status = res.status_code

    # When deleting an UpCloud server, HTTP 409 means the server has not stopped yet and a retry is needed
    # Example error payload:
    # {
    #     'error': {
    #         'error_code': 'SERVER_STATE_ILLEGAL',
    #         'error_message': "The operation is not allowed while the server ... is in state 'started'."
    #     }
    # }

    if 200 <= status < 300:
        return

    if status == 404:
        return

    if 500 <= status < 600:
        return

    raise dramatiq.errors.Retry(f"Unexpected status code: {status}")
