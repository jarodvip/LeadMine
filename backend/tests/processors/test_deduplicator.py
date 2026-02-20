"""
去重算法测试 - 修复版
"""

import pytest
from app.processors.deduplicator import Deduplicator, deduplicator, check_duplicate


class TestDeduplicator:
    """测试去重器"""

    @pytest.fixture
    def dedup(self):
        """创建去重器实例"""
        return Deduplicator()

    def test_compute_hash(self, dedup):
        """测试 SimHash 计算"""
        text1 = "这是一段测试文本"
        text2 = "这是另一段不同的文本内容"

        hash1 = dedup.compute_hash(text1)
        hash2 = dedup.compute_hash(text2)

        assert hash1 is not None
        assert hash2 is not None
        assert hash1 != hash2

    def test_same_text_same_hash(self, dedup):
        """测试相同文本产生相同 Hash"""
        text = "完全相同的文本内容"
        hash1 = dedup.compute_hash(text)
        hash2 = dedup.compute_hash(text)
        assert hash1 == hash2

    def test_is_duplicate_false(self, dedup):
        """测试不重复内容"""
        text1 = "今天天气很好，适合出门散步"
        text2 = "人工智能技术发展迅速"

        # 首次添加
        is_dup1 = dedup.is_duplicate(text1, source="test")
        assert is_dup1 is False

        # 不同内容不重复
        is_dup2 = dedup.is_duplicate(text2, source="test")
        assert is_dup2 is False

    def test_is_duplicate_true(self, dedup):
        """测试重复内容检测"""
        text = "36氪首发｜某某公司完成1亿元A轮融资"

        # 首次不重复
        is_dup1 = dedup.is_duplicate(text, source="test_dup")
        assert is_dup1 is False

        # 再次检测应该重复
        is_dup2 = dedup.is_duplicate(text, source="test_dup")
        assert is_dup2 is True

    def test_empty_text(self, dedup):
        """测试空文本处理"""
        text = ""
        hash_value = dedup.compute_hash(text)
        assert hash_value is not None

    def test_hamming_distance(self, dedup):
        """测试海明距离计算"""
        # 两个不同的hash
        hash1 = 0b10101010
        hash2 = 0b10101011

        distance = dedup._hamming_distance(hash1, hash2)
        assert distance == 1

    def test_clear(self, dedup):
        """测试清除存储"""
        text = "测试内容"
        dedup.is_duplicate(text, source="clear_test")

        # 清除
        dedup.clear(source="clear_test")

        # 再次应该不重复
        is_dup = dedup.is_duplicate(text, source="clear_test")
        assert is_dup is False


class TestGlobalDeduplicator:
    """测试全局去重器"""

    def test_check_duplicate(self):
        """测试全局检查函数"""
        text = "全局测试内容"

        # 首次不重复
        is_dup1 = check_duplicate(text, source="global_test")
        assert is_dup1 is False

        # 再次重复
        is_dup2 = check_duplicate(text, source="global_test")
        assert is_dup2 is True


class TestDeduplicationScenarios:
    """测试各种重复场景"""

    def test_exact_duplicate(self):
        """测试完全重复"""
        dedup = Deduplicator()
        text = "完全相同的内容"

        dedup.is_duplicate(text, source="exact")
        assert dedup.is_duplicate(text, source="exact") is True

    def test_similar_text(self):
        """测试相似文本"""
        dedup = Deduplicator()
        text1 = "人工智能公司完成1亿元融资"
        text2 = "人工智能公司完成1亿元A轮融资"

        dedup.is_duplicate(text1, source="similar")
        # 相似文本可能被检测为重复，取决于阈值
