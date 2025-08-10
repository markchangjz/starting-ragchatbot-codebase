import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import os
import sys

# Add backend to path so we can import modules
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Mock external dependencies before importing
sys.modules['chromadb'] = MagicMock()
sys.modules['anthropic'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()

from config import Config


@pytest.fixture
def test_config():
    """Provide a test configuration with temporary paths"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        config.CHROMA_PATH = os.path.join(temp_dir, "test_chroma_db")
        config.ANTHROPIC_API_KEY = "test-key"
        yield config


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing without API calls"""
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_course():
    """Sample course data for testing"""
    # Import here to avoid circular import issues
    from models import Course, Lesson
    return Course(
        title="Test Course",
        lessons=[
            Lesson(title="Lesson 1", link="http://example.com/lesson1"),
            Lesson(title="Lesson 2")
        ]
    )


@pytest.fixture
def sample_course_chunk():
    """Sample course chunk for testing"""
    # Import here to avoid circular import issues
    from models import CourseChunk
    return CourseChunk(
        course_title="Test Course",
        lesson_title="Lesson 1",
        content="This is sample content for testing the RAG system.",
        chunk_id="chunk_1"
    )


@pytest.fixture
def mock_vector_store():
    """Mock vector store to avoid ChromaDB dependencies in tests"""
    with patch("vector_store.VectorStore") as mock_store:
        store_instance = Mock()
        store_instance.add_chunks.return_value = None
        store_instance.search.return_value = [
            ("This is sample content", {"course_title": "Test Course", "lesson_title": "Lesson 1"})
        ]
        store_instance.get_collection_info.return_value = {"total_chunks": 5}
        mock_store.return_value = store_instance
        yield store_instance


@pytest.fixture
def mock_document_processor():
    """Mock document processor for testing"""
    with patch("document_processor.DocumentProcessor") as mock_processor:
        # Import here to avoid circular import issues
        from models import Course, Lesson, CourseChunk
        
        processor_instance = Mock()
        processor_instance.process_document.return_value = (
            Course(title="Test Course", lessons=[Lesson(title="Test Lesson")]),
            [CourseChunk(
                course_title="Test Course",
                lesson_title="Test Lesson", 
                content="Sample content",
                chunk_id="test_chunk_1"
            )]
        )
        mock_processor.return_value = processor_instance
        yield processor_instance


@pytest.fixture
def temp_docs_folder():
    """Create a temporary docs folder with sample files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_path = Path(temp_dir) / "docs"
        docs_path.mkdir()
        
        # Create sample document
        sample_doc = docs_path / "sample.txt"
        sample_doc.write_text("This is a sample document for testing.")
        
        yield str(docs_path)


@pytest.fixture
def mock_rag_system(test_config, mock_anthropic_client, mock_vector_store, mock_document_processor):
    """Mock RAG system with all dependencies mocked"""
    with patch("rag_system.RAGSystem") as mock_rag:
        rag_instance = Mock()
        rag_instance.query.return_value = ("Test answer", ["Test source"])
        rag_instance.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Test Course"]
        }
        rag_instance.session_manager.create_session.return_value = "test-session-123"
        mock_rag.return_value = rag_instance
        yield rag_instance


@pytest.fixture
def test_query_data():
    """Sample query request data"""
    return {
        "query": "What is the main topic?",
        "session_id": "test-session-123"
    }


@pytest.fixture 
def expected_query_response():
    """Expected query response format"""
    return {
        "answer": "Test answer",
        "sources": ["Test source"],
        "session_id": "test-session-123"
    }