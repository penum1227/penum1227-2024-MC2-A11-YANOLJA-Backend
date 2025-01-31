# app/utils/retry_decorator.py

import time
import logging
from functools import wraps

logger = logging.getLogger("kbo_crawler")

def retry_sync(max_retries=3, delay=2):
    """
    동기 함수용 리트라이 데코레이터.
    최대 재시도 횟수와 재시도 간격을 설정할 수 있습니다.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    logger.warning(f"Retry {retries}/{max_retries} for function {func.__name__} due to error: {e}")
                    time.sleep(delay)
            logger.error(f"All {max_retries} retries failed for function {func.__name__}")
            raise Exception(f"Function {func.__name__} failed after {max_retries} retries.")
        return wrapper
    return decorator
