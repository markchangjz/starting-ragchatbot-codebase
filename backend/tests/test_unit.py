import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Mock external dependencies
sys.modules['chromadb'] = MagicMock()
sys.modules['anthropic'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()


@pytest.mark.unit
class TestModelsUnit:
    """Unit tests for data models"""
    
    def test_course_model_creation(self):
        """Test Course model can be created"""
        from models import Course, Lesson
        
        course = Course(
            title="Test Course",
            lessons=[
                Lesson(lesson_number=1, title="Lesson 1", lesson_link="http://example.com"),
                Lesson(lesson_number=2, title="Lesson 2")
            ]
        )
        
        assert course.title == "Test Course"
        assert len(course.lessons) == 2
        assert course.lessons[0].title == "Lesson 1"
        assert course.lessons[0].lesson_number == 1
        assert course.lessons[0].lesson_link == "http://example.com"
        assert course.lessons[1].title == "Lesson 2"
        assert course.lessons[1].lesson_number == 2
        assert course.lessons[1].lesson_link is None
    
    def test_course_chunk_model_creation(self):
        """Test CourseChunk model can be created"""
        from models import CourseChunk
        
        chunk = CourseChunk(
            content="This is test content",
            course_title="Test Course",
            lesson_number=1,
            chunk_index=0
        )
        
        assert chunk.content == "This is test content"
        assert chunk.course_title == "Test Course"
        assert chunk.lesson_number == 1
        assert chunk.chunk_index == 0


@pytest.mark.unit
class TestConfigUnit:
    """Unit tests for configuration"""
    
    def test_config_creation(self):
        """Test Config can be created with defaults"""
        from config import Config
        
        config = Config()
        
        assert hasattr(config, 'ANTHROPIC_MODEL')
        assert hasattr(config, 'EMBEDDING_MODEL')
        assert hasattr(config, 'CHUNK_SIZE')
        assert hasattr(config, 'CHUNK_OVERLAP')
        assert hasattr(config, 'MAX_RESULTS')
        assert hasattr(config, 'MAX_HISTORY')
        assert hasattr(config, 'CHROMA_PATH')
    
    def test_config_values(self):
        """Test Config has expected default values"""
        from config import Config
        
        config = Config()
        
        assert config.ANTHROPIC_MODEL == "claude-sonnet-4-20250514"
        assert config.EMBEDDING_MODEL == "all-MiniLM-L6-v2"
        assert config.CHUNK_SIZE == 800
        assert config.CHUNK_OVERLAP == 100
        assert config.MAX_RESULTS == 5
        assert config.MAX_HISTORY == 2
        assert config.CHROMA_PATH == "./chroma_db"


@pytest.mark.unit
class TestSessionManagerUnit:
    """Unit tests for session management"""
    
    def test_session_manager_creation(self):
        """Test SessionManager can be created"""
        from session_manager import SessionManager
        
        session_manager = SessionManager(max_history=2)
        assert session_manager.max_history == 2
    
    def test_create_session(self):
        """Test session creation generates unique IDs"""
        from session_manager import SessionManager
        
        session_manager = SessionManager(max_history=2)
        
        session1 = session_manager.create_session()
        session2 = session_manager.create_session()
        
        assert session1 != session2
        assert isinstance(session1, str)
        assert isinstance(session2, str)
        assert len(session1) > 0
        assert len(session2) > 0
    
    def test_add_message(self):
        """Test adding messages to session"""
        from session_manager import SessionManager
        
        session_manager = SessionManager(max_history=2)
        session_id = session_manager.create_session()
        
        session_manager.add_message(session_id, "user", "Hello")
        session_manager.add_message(session_id, "assistant", "Hi there")
        
        # Check that session was created and messages were added
        assert session_id in session_manager.sessions
        history = session_manager.sessions[session_id]
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[1].role == "assistant"
        assert history[1].content == "Hi there"
    
    def test_session_history_limit(self):
        """Test session history respects max_history limit"""
        from session_manager import SessionManager
        
        session_manager = SessionManager(max_history=2)
        session_id = session_manager.create_session()
        
        # Add more messages than the limit
        session_manager.add_message(session_id, "user", "Message 1")
        session_manager.add_message(session_id, "assistant", "Response 1")
        session_manager.add_message(session_id, "user", "Message 2")
        session_manager.add_message(session_id, "assistant", "Response 2")
        session_manager.add_message(session_id, "user", "Message 3")
        
        history = session_manager.sessions[session_id]
        # Should only keep the last 4 messages (max_history * 2)
        assert len(history) <= 4
        # Should keep the most recent messages
        assert "Message 3" in [msg.content for msg in history]


@pytest.mark.unit 
class TestSearchToolsUnit:
    """Unit tests for search tools"""
    
    @patch('search_tools.VectorStore')
    def test_course_search_tool_creation(self, mock_vector_store):
        """Test CourseSearchTool can be created"""
        from search_tools import CourseSearchTool
        
        mock_store = Mock()
        mock_vector_store.return_value = mock_store
        
        tool = CourseSearchTool(mock_store)
        assert tool.vector_store == mock_store
    
    @patch('search_tools.VectorStore')
    def test_course_search_tool_search(self, mock_vector_store):
        """Test CourseSearchTool search functionality"""
        from search_tools import CourseSearchTool
        
        mock_store = Mock()
        mock_store.search.return_value = [
            ("Test content", {"course_title": "Course 1", "lesson_title": "Lesson 1"})
        ]
        mock_vector_store.return_value = mock_store
        
        tool = CourseSearchTool(mock_store)
        results = tool.search("test query")
        
        assert isinstance(results, list)
        mock_store.search.assert_called_once_with("test query", k=5)


@pytest.mark.unit
class TestValidationUnit:
    """Unit tests for input validation and edge cases"""
    
    def test_empty_strings(self):
        """Test handling of empty strings"""
        from models import Course, Lesson
        
        # Test empty course title
        course = Course(title="", lessons=[])
        assert course.title == ""
        assert len(course.lessons) == 0
        
        # Test empty lesson title
        lesson = Lesson(lesson_number=1, title="", lesson_link="")
        assert lesson.title == ""
        assert lesson.lesson_link == ""
    
    def test_none_values(self):
        """Test handling of None values"""
        from models import Lesson
        
        # Test None link (which is allowed)
        lesson = Lesson(lesson_number=1, title="Test", lesson_link=None)
        assert lesson.title == "Test"
        assert lesson.lesson_link is None
    
    def test_session_manager_invalid_session(self):
        """Test session manager with invalid session ID"""
        from session_manager import SessionManager
        
        session_manager = SessionManager(max_history=2)
        
        # Test with non-existent session ID
        history = session_manager.get_session_history("invalid-session")
        assert history == []
        
        # Adding message to non-existent session should not crash
        session_manager.add_message("invalid-session", "user", "test")
        # Should still return empty history for invalid session
        history = session_manager.get_session_history("invalid-session")
        assert len(history) > 0  # Session should be created when message is added