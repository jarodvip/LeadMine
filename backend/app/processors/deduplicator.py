"""
SimHash去重服务
"""

import redis
from simhash import Simhash
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class Deduplicator:
    """SimHash去重器"""

    def __init__(self, hash_bits: int = 64, threshold: int = 3):
        """
        初始化去重器
        Args:
            hash_bits: SimHash位数
            threshold: 海明距离阈值，超过此值认为不重复
        """
        self.hash_bits = hash_bits
        self.threshold = threshold
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url, decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，将使用内存存储: {e}")
            self.redis_client = None

    def _preprocess(self, text: str) -> str:
        """文本预处理"""
        if not text:
            return ""
        # 转小写
        text = text.lower()
        # 移除特殊字符，保留中文、英文、数字
        import re

        text = re.sub(r"[^\w\s\u4e00-\u9fff]", "", text)
        # 移除多余空格
        text = " ".join(text.split())
        return text

    def compute_hash(self, text: str) -> int:
        """
        计算SimHash值
        Args:
            text: 待计算文本
        Returns:
            SimHash值
        """
        text = self._preprocess(text)
        if not text:
            return 0
        return Simhash(text, f=self.hash_bits).value

    def is_duplicate(self, content: str, source: str = "default") -> bool:
        """
        检查内容是否重复
        Args:
            content: 待检查内容
            source: 来源标识
        Returns:
            True表示重复，False表示不重复
        """
        current_hash = self.compute_hash(content)

        if self.redis_client:
            return self._check_redis(current_hash, source)
        else:
            return self._check_memory(current_hash, source)

    def _check_redis(self, current_hash: int, source: str) -> bool:
        """使用Redis检查重复"""
        key = f"simhash:{source}"

        try:
            # 获取所有已存储的hash
            stored_hashes = self.redis_client.smembers(key)

            if not stored_hashes:
                # 首次存储
                self.redis_client.sadd(key, str(current_hash))
                return False

            # 计算海明距离
            for stored in stored_hashes:
                stored_int = int(stored)
                distance = self._hamming_distance(current_hash, stored_int)

                if distance <= self.threshold:
                    logger.debug(f"发现重复内容，海明距离: {distance}")
                    return True

            # 不重复，存储新hash
            self.redis_client.sadd(key, str(current_hash))

            # 限制存储数量，避免内存过大
            if self.redis_client.scard(key) > 10000:
                # 移除最早的1000个
                self.redis_client.spop(key, 1000)

            return False

        except Exception as e:
            logger.error(f"Redis检查失败: {e}")
            return False

    # 内存存储
    _memory_store = {}

    def _check_memory(self, current_hash: int, source: str) -> bool:
        """使用内存检查重复"""
        if source not in self._memory_store:
            self._memory_store[source] = set()

        stored_hashes = self._memory_store[source]

        for stored in stored_hashes:
            distance = self._hamming_distance(current_hash, stored)
            if distance <= self.threshold:
                return True

        stored_hashes.add(current_hash)

        # 限制存储数量
        if len(stored_hashes) > 5000:
            # 移除一半
            self._memory_store[source] = set(list(stored_hashes)[-2500:])

        return False

    def _hamming_distance(self, hash1: int, hash2: int) -> int:
        """计算海明距离"""
        x = hash1 ^ hash2
        distance = 0
        while x:
            distance += 1
            x &= x - 1
        return distance

    def add_hash(self, content: str, source: str = "default"):
        """手动添加hash"""
        current_hash = self.compute_hash(content)

        if self.redis_client:
            key = f"simhash:{source}"
            self.redis_client.sadd(key, str(current_hash))
        else:
            if source not in self._memory_store:
                self._memory_store[source] = set()
            self._memory_store[source].add(current_hash)

    def clear(self, source: str = None):
        """清除存储的hash"""
        if self.redis_client:
            if source:
                self.redis_client.delete(f"simhash:{source}")
            else:
                # 清除所有
                keys = self.redis_client.keys("simhash:*")
                if keys:
                    self.redis_client.delete(*keys)
        else:
            if source:
                self._memory_store.pop(source, None)
            else:
                self._memory_store.clear()


# 全局去重器实例
deduplicator = Deduplicator()


def check_duplicate(content: str, source: str = "default") -> bool:
    """检查内容是否重复"""
    return deduplicator.is_duplicate(content, source)


def add_content(content: str, source: str = "default"):
    """添加内容到去重存储"""
    deduplicator.add_hash(content, source)
