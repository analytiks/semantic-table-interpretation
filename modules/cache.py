"""Redis cache query"""
import hashlib
import redis 
import json

redis_cache = redis.StrictRedis(host='localhost', port=6379, db=0)

def put(query, result):
    query_hash = hashlib.md5(query).hexdigest()
    redis_cache.set(query_hash, json.dumps(result))

def get(query):
    query_hash = hashlib.md5(query).hexdigest()
    result = redis_cache.get(query_hash)
    if result is None:
        return None
    return json.loads(result)