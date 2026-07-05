import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from logger import logger
from config import config

class EnrichmentCache:
    def __init__(self):
        # Ensure directory exists
        db_dir = os.path.dirname(config.CACHE_DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = config.CACHE_DB_PATH
        self.ttl_seconds = config.CACHE_TTL_SECONDS
        
        # Create table (minimal, no index for compatibility)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS company_cache (
                        company_name TEXT PRIMARY KEY,
                        data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
            logger.info(f"✅ Cache initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize cache: {e}")
            raise
    
    def get(self, company_name: str):
        try:
            cache_expiry = datetime.now() - timedelta(seconds=self.ttl_seconds)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM company_cache WHERE company_name = ? AND created_at > ?",
                    (company_name.lower(), cache_expiry)
                )
                row = cursor.fetchone()
                if row:
                    logger.info(f"✅ Cache HIT: {company_name}")
                    return json.loads(row[0])
                logger.info(f"❌ Cache MISS: {company_name}")
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, company_name: str, data: Dict):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO company_cache (company_name, data) VALUES (?, ?)",
                    (company_name.lower(), json.dumps(data))
                )
                conn.commit()
                logger.info(f"💾 Cache SET: {company_name}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def get_cache_stats(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute("SELECT COUNT(*) FROM company_cache").fetchone()[0]
                cache_expiry = datetime.now() - timedelta(seconds=self.ttl_seconds)
                fresh = conn.execute(
                    "SELECT COUNT(*) FROM company_cache WHERE created_at > ?",
                    (cache_expiry,)
                ).fetchone()[0]
                return {
                    "total_cached": total,
                    "fresh_cached": fresh,
                    "stale_cached": total - fresh,
                    "ttl_hours": self.ttl_seconds / 3600
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"total_cached": 0, "fresh_cached": 0, "stale_cached": 0, "ttl_hours": 0}
    
    def clear_stale(self):
        try:
            cache_expiry = datetime.now() - timedelta(seconds=self.ttl_seconds)
            with sqlite3.connect(self.db_path) as conn:
                deleted = conn.execute(
                    "DELETE FROM company_cache WHERE created_at < ?",
                    (cache_expiry,)
                )
                conn.commit()
                logger.info(f"🗑️ Cleared {deleted.rowcount} stale cache entries")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

# Global instance
cache = EnrichmentCache()