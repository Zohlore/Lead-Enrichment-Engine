from config import config
from logger import logger
print("Cache path:", config.CACHE_DB_PATH)
print("TTL:", config.CACHE_TTL_SECONDS)

try:
    from cache import cache
    print("✅ Cache imported successfully")
    cache.set("test", {"name": "Test"})
    print(cache.get("test"))
except Exception as e:
    print("❌ Error:", e)
    import traceback
    traceback.print_exc()