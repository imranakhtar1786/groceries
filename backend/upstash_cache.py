import json
from django.core.cache.backends.base import BaseCache, DEFAULT_TIMEOUT
from upstash_redis import Redis
import os

class UpstashRESTCache(BaseCache):
    """
    A custom Django cache backend that uses the Upstash Redis REST API.
    This avoids the need for a TCP connection which is beneficial in serverless environments.
    """
    def __init__(self, server, params):
        super().__init__(params)
        # Using environment variables directly here as per configuration strategy
        url = os.environ.get('UPSTASH_REDIS_REST_URL')
        token = os.environ.get('UPSTASH_REDIS_REST_TOKEN')
        if not url or not token:
            raise ValueError("UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be set in environment variables.")
        self._client = Redis(url=url, token=token)

    def _pack_value(self, value):
        # We use JSON serialization for the REST API
        return json.dumps(value)

    def _unpack_value(self, value):
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_and_validate_key(key, version=version)
        val = self._pack_value(value)
        if timeout == DEFAULT_TIMEOUT:
            timeout = self.default_timeout
            
        if timeout is None:
            return bool(self._client.set(key, val, nx=True))
        elif timeout > 0:
            return bool(self._client.set(key, val, ex=timeout, nx=True))
        return False

    def get(self, key, default=None, version=None):
        key = self.make_and_validate_key(key, version=version)
        val = self._client.get(key)
        if val is None:
            return default
        return self._unpack_value(val)

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_and_validate_key(key, version=version)
        val = self._pack_value(value)
        if timeout == DEFAULT_TIMEOUT:
            timeout = self.default_timeout
            
        if timeout is None:
            self._client.set(key, val)
        elif timeout > 0:
            self._client.set(key, val, ex=timeout)

    def delete(self, key, version=None):
        key = self.make_and_validate_key(key, version=version)
        self._client.delete(key)

    def clear(self):
        self._client.flushdb()
