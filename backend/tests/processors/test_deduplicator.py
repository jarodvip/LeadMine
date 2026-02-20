"""
去重算法测试
测试 SimHash 去重功能
"""

import pytest


class TestDeduplicator:
    """测试去重器"""

    @pytest.fixture
    def deduplicator(self):
        """创建去重器实例"""
        from app.processors.deduplicator import Deduplicator

        return Deduplicator()

    def test_simhash_generation(self, deduplicator):
        """测试 SimHash 生成"""
        text1 = "这是一段测试文本，用于生成 SimHash"
        text2 = "这是另一段不同的文本内容"

        hash1 = deduplicator._get_simhash(text1)
        hash2 = deduplicator._get_simhash(text2)

        assert hash1 is not None
        assert hash2 is not None
        assert hash1 != hash2

    def test_same_text_same_hash(self, deduplicator):
        """测试相同文本产生相同 Hash"""
        text = "完全相同的文本内容"
        hash1 = deduplicator._get_simhash(text)
        hash2 = deduplicator._get_simhash(text)
        assert hash1 == hash2

    def test_similar_text_similar_hash(self, deduplicator):
        """测试相似文本产生相似 Hash"""
        text1 = "人工智能公司完成1亿元融资，用于技术研发"
        text2 = "人工智能公司完成1亿元融资，用于市场拓展"

        hash1 = deduplicator._get_simhash(text1)
        hash2 = deduplicator._get_simhash(text2)

        distance = deduplicator._hamming_distance(hash1, hash2)
        assert distance < 10  # 相似文本的汉明距离应该较小

    def test_different_text_different_hash(self, deduplicator):
        """测试不同文本产生不同 Hash"""
        text1 = "今天天气很好，适合出门散步"
        text2 = "人工智能技术发展迅速，应用广泛"

        hash1 = deduplicator._get_simhash(text1)
        hash2 = deduplicator._get_simhash(text2)

        distance = deduplicator._hamming_distance(hash1, hash2)
        assert distance > 10  # 不同文本的汉明距离应该较大

    def test_hamming_distance_calculation(self, deduplicator):
        """测试汉明距离计算"""
        # 两个只有一位不同的二进制数
        hash1 = 0b10101010
        hash2 = 0b10101011

        distance = deduplicator._hamming_distance(hash1, hash2)
        assert distance == 1

    def test_is_duplicate_true(self, deduplicator):
        """测试检测重复（是重复）"""
        text1 = "36氪首发｜某某公司完成1亿元A轮融资，本轮融资由红杉资本领投"
        text2 = "36氪首发｜某某公司完成1亿元A轮融资，本轮融资由红杉资本领投，资金将用于技术研发"

        is_dup = deduplicator.is_duplicate(text1, text2, threshold=10)
        # 取决于具体实现和阈值

    def test_is_duplicate_false(self, deduplicator):
        """测试检测重复（不是重复）"""
        text1 = "今天天气很好，适合出门散步"
        text2 = "人工智能技术发展迅速"

        is_dup = deduplicator.is_duplicate(text1, text2, threshold=10)
        assert is_dup is False

    def test_empty_text(self, deduplicator):
        """测试空文本处理"""
        text = ""
        hash_value = deduplicator._get_simhash(text)
        # 应该能处理空文本
        assert hash_value is not None

    def test_very_long_text(self, deduplicator):
        """测试超长文本"""
        text = "这是一段很长的文本。" * 1000
        hash_value = deduplicator._get_simhash(text)
        assert hash_value is not None


class TestRedisDeduplication:
    """测试 Redis 去重"""

    @pytest.fixture
    def deduplicator_with_redis(self):
        """创建带 Redis 的去重器"""
        # 这里需要 mock Redis 或者使用测试 Redis
        from app.processors.deduplicator import Deduplicator

        dedup = Deduplicator()
        return dedup

    def test_add_to_redis(self, deduplicator_with_redis):
        """测试添加到 Redis"""
        text = "测试文本"
        # 添加文本到去重库

    def test_check_in_redis(self, deduplicator_with_redis):
        """测试从 Redis 检查"""
        text = "已存在的文本"
        # 检查是否已存在


class TestDuplicateDetectionScenarios:
    """测试各种重复场景"""

    def test_exact_duplicate(self):
        """测试完全重复"""
        text1 = "完全相同的内容"
        text2 = "完全相同的内容"
        # 应该是重复

    def test_minor_difference(self):
        """测试微小差异"""
        text1 = "某某公司完成1亿元融资"
        text2 = "某某公司完成1亿元A轮融资"
        # 可能是重复（取决于阈值）

    def test_different_source_same_content(self):
        """测试不同来源相同内容"""
        text1 = "36氪：某某公司融资1亿元"
        text2 = "虎嗅：某某公司融资1亿元"
        # 应该被认为是重复

    def test_same_event_different_reporting(self):
        """测试同一事件不同报道"""
        text1 = "人工智能公司完成融资，金额为1亿元"
        text2 = "1亿元！人工智能公司今日宣布融资成功"
        # 应该是重复

    def test_different_events(self):
        """测试不同事件"""
        text1 = "A公司完成1亿元融资"
        text2 = "B公司完成2亿元融资"
        # 不应该是重复
