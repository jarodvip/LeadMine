"""
ArticleCleaner 完整测试 - 提高覆盖率
"""

import pytest
from app.processors.cleaner import ArticleCleaner, clean_article, sanitize_input


class TestArticleCleanerInit:
    """测试初始化"""

    def test_init(self):
        """测试初始化"""
        cleaner = ArticleCleaner()
        assert cleaner.html_tags_pattern is not None
        assert cleaner.extra_spaces_pattern is not None


class TestCleanHtml:
    """测试 HTML 清洗"""

    @pytest.fixture
    def cleaner(self):
        return ArticleCleaner()

    def test_clean_html_basic(self, cleaner):
        """测试基础 HTML 清洗"""
        html = "<p>这是一段文本</p>"
        result = cleaner.clean_html(html)
        assert "<p>" not in result
        assert "这是一段文本" in result

    def test_clean_html_with_script(self, cleaner):
        """测试移除 script 标签"""
        html = "<p>文本</p><script>alert('xss')</script>"
        result = cleaner.clean_html(html)
        assert "<script>" not in result
        assert "alert" not in result

    def test_clean_html_with_style(self, cleaner):
        """测试移除 style 标签"""
        html = "<style>body{color:red}</style><p>文本</p>"
        result = cleaner.clean_html(html)
        assert "<style>" not in result
        assert "body{color:red}" not in result

    def test_clean_html_empty(self, cleaner):
        """测试空 HTML"""
        result = cleaner.clean_html("")
        assert result == ""

    def test_clean_html_none(self, cleaner):
        """测试 None 输入"""
        result = cleaner.clean_html(None)
        assert result == ""

    def test_clean_html_complex(self, cleaner):
        """测试复杂 HTML"""
        html = """
        <html>
        <body>
            <h1>标题</h1>
            <p>段落1</p>
            <p>段落2</p>
            <script>evil()</script>
        </body>
        </html>
        """
        result = cleaner.clean_html(html)
        assert "标题" in result
        assert "段落1" in result
        assert "evil()" not in result

    def test_clean_html_with_entities(self, cleaner):
        """测试 HTML 实体"""
        html = "<p>&lt;test&gt; &amp; &quot;quote&quot;</p>"
        result = cleaner.clean_html(html)
        assert "<test>" in result
        assert "&" in result
        assert '"' in result


class TestSimpleStripTags:
    """测试简单标签移除"""

    @pytest.fixture
    def cleaner(self):
        return ArticleCleaner()

    def test_simple_strip(self, cleaner):
        """测试简单移除"""
        html = "<div>文本</div>"
        result = cleaner._simple_strip_tags(html)
        assert "<div>" not in result
        assert "文本" in result


class TestCleanText:
    """测试文本清理"""

    @pytest.fixture
    def cleaner(self):
        return ArticleCleaner()

    def test_clean_text_whitespace(self, cleaner):
        """测试清理多余空格"""
        text = "这是    很多   空格"
        result = cleaner._clean_text(text)
        assert "  " not in result

    def test_clean_text_newlines(self, cleaner):
        """测试清理换行"""
        text = "这是\n\n\n多行"
        result = cleaner._clean_text(text)
        assert result.strip() != ""

    def test_clean_text_empty(self, cleaner):
        """测试空文本"""
        result = cleaner._clean_text("")
        assert result == ""

    def test_clean_text_none(self, cleaner):
        """测试 None"""
        result = cleaner._clean_text(None)
        assert result == ""


class TestSanitizeXSS:
    """测试 XSS 过滤"""

    @pytest.fixture
    def cleaner(self):
        return ArticleCleaner()

    def test_sanitize_script_tag(self, cleaner):
        """测试过滤 script 标签"""
        html = "<script>alert('xss')</script>正常内容"
        result = cleaner.sanitize_xss(html)
        assert "<script>" not in result
        assert "alert" not in result
        assert "正常内容" in result

    def test_sanitize_iframe_tag(self, cleaner):
        """测试过滤 iframe"""
        html = "<iframe src='evil.com'></iframe>内容"
        result = cleaner.sanitize_xss(html)
        assert "<iframe>" not in result
        assert "evil.com" not in result

    def test_sanitize_event_handler(self, cleaner):
        """测试过滤事件处理器"""
        html = "<img onerror='alert(1)' src='x'>图片"
        result = cleaner.sanitize_xss(html)
        assert "onerror" not in result.lower()

    def test_sanitize_javascript_protocol(self, cleaner):
        """测试过滤 javascript: 协议"""
        html = "<a href='javascript:alert(1)'>点击</a>"
        result = cleaner.sanitize_xss(html)
        assert "javascript:" not in result.lower()

    def test_sanitize_empty(self, cleaner):
        """测试空输入"""
        result = cleaner.sanitize_xss("")
        assert result == ""

    def test_sanitize_none(self, cleaner):
        """测试 None"""
        result = cleaner.sanitize_xss(None)
        assert result == ""

    def test_sanitize_object_tag(self, cleaner):
        """测试过滤 object 标签"""
        html = "<object data='evil.swf'></object>内容"
        result = cleaner.sanitize_xss(html)
        assert "<object>" not in result

    def test_sanitize_embed_tag(self, cleaner):
        """测试过滤 embed 标签"""
        html = "<embed src='evil.swf'>内容"
        result = cleaner.sanitize_xss(html)
        assert "<embed>" not in result


class TestSimpleSanitizeXSS:
    """测试简单 XSS 过滤（备用方案）"""

    @pytest.fixture
    def cleaner(self):
        return ArticleCleaner()

    def test_simple_sanitize(self, cleaner):
        """测试简单过滤"""
        text = "<script>alert(1)</script>正常"
        result = cleaner._simple_sanitize_xss(text)
        assert "<script>" not in result
        assert "正常" in result


class TestExtractContent:
    """测试内容提取"""

    @pytest.fixture
    def cleaner(self):
        return ArticleCleaner()

    def test_extract_content_from_html(self, cleaner):
        """测试从 HTML 提取内容"""
        html = """
        <html>
        <head><title>测试标题</title></head>
        <body>
            <article>文章内容</article>
        </body>
        </html>
        """
        result = cleaner.extract_content_from_html(html, "http://test.com")
        assert "title" in result
        assert "content" in result
        assert result["title"] == "测试标题"

    def test_extract_content_no_article(self, cleaner):
        """测试无 article 标签"""
        html = """
        <html>
        <head><title>标题</title></head>
        <body>
            <div class="content">内容</div>
        </body>
        </html>
        """
        result = cleaner.extract_content_from_html(html)
        assert result["title"] == "标题"


class TestExtractAuthor:
    """测试作者提取"""

    @pytest.fixture
    def cleaner(self):
        return ArticleCleaner()

    def test_extract_author_meta(self, cleaner):
        """测试从 meta 提取作者"""
        html = '<meta name="author" content="张三">'
        result = cleaner.extract_author(html)
        assert result == "张三"

    def test_extract_author_class(self, cleaner):
        """测试从 class 提取作者"""
        html = '<span class="author">李四</span>'
        result = cleaner.extract_author(html)
        assert result == "李四"

    def test_extract_author_empty(self, cleaner):
        """测试无作者"""
        html = "<p>文章内容</p>"
        result = cleaner.extract_author(html)
        assert result == ""


class TestExtractPublishedTime:
    """测试发布时间提取"""

    @pytest.fixture
    def cleaner(self):
        return ArticleCleaner()

    def test_extract_time_meta(self, cleaner):
        """测试从 meta 提取时间"""
        html = '<meta property="article:published_time" content="2026-02-20">'
        result = cleaner.extract_published_time(html)
        assert result == "2026-02-20"

    def test_extract_time_tag(self, cleaner):
        """测试从 time 标签提取"""
        html = '<time datetime="2026-02-20T10:00:00">2026-02-20</time>'
        result = cleaner.extract_published_time(html)
        assert "2026-02-20" in result

    def test_extract_time_empty(self, cleaner):
        """测试无时间"""
        html = "<p>文章内容</p>"
        result = cleaner.extract_published_time(html)
        assert result is None


class TestCleanArticle:
    """测试文章清洗函数"""

    def test_clean_article_full(self):
        """测试完整文章清洗"""
        article = {
            "title": "<p>标题</p>",
            "content": "<script>alert(1)</script>内容",
            "summary": "<b>摘要</b>",
        }
        result = clean_article(article)
        assert "<p>" not in result["title"]
        assert "<script>" not in result["content"]
        assert "<b>" not in result["summary"]

    def test_clean_article_empty(self):
        """测试空文章"""
        article = {}
        result = clean_article(article)
        assert result == {}


class TestSanitizeInput:
    """测试通用输入净化"""

    def test_sanitize_input_script(self):
        """测试净化 script"""
        text = "<script>alert(1)</script>正常"
        result = sanitize_input(text)
        assert "<script>" not in result
        assert "正常" in result

    def test_sanitize_input_empty(self):
        """测试空输入"""
        result = sanitize_input("")
        assert result == ""

    def test_sanitize_input_none(self):
        """测试 None"""
        result = sanitize_input(None)
        assert result == ""
