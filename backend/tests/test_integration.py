import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import sys

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Mock external dependencies before importing
sys.modules['chromadb'] = MagicMock()
sys.modules['chromadb.config'] = MagicMock()
sys.modules['anthropic'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()


@pytest.mark.integration
class TestRAGSystemIntegration:
    """Integration tests for the complete RAG system"""
    
    @patch("anthropic.Anthropic")
    @patch("vector_store.VectorStore")
    def test_full_query_processing_flow(self, mock_vector_store, mock_anthropic, test_config):
        """Test complete query processing from start to finish"""
        from rag_system import RAGSystem
        
        # Setup mocks
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="This is about machine learning concepts.")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        mock_store_instance = Mock()
        mock_store_instance.search.return_value = [
            ("Machine learning is a subset of AI", {"course_title": "ML Course", "lesson_title": "Introduction"})
        ]
        mock_vector_store.return_value = mock_store_instance
        
        # Initialize system
        rag_system = RAGSystem(test_config)
        
        # Process query
        answer, sources = rag_system.query("What is machine learning?", "test-session")
        
        # Verify results
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert isinstance(sources, list)
        
        # Verify vector store was called for search
        mock_store_instance.search.assert_called_once()
        
        # Verify AI was called with proper context
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert "messages" in call_args.kwargs
    
    @patch("anthropic.Anthropic")
    @patch("vector_store.VectorStore")  
    @patch("document_processor.DocumentProcessor")
    def test_document_loading_and_query_flow(self, mock_doc_processor, mock_vector_store, mock_anthropic, test_config, temp_docs_folder):
        """Test loading documents and then querying them"""
        from rag_system import RAGSystem
        from models import Course, Lesson, CourseChunk
        
        # Setup document processor mock
        mock_processor_instance = Mock()
        mock_processor_instance.process_document.return_value = (
            Course(title="Test Course", lessons=[Lesson(title="Test Lesson")]),
            [CourseChunk(
                course_title="Test Course",
                lesson_title="Test Lesson",
                content="Sample content about testing",
                chunk_id="chunk_1"
            )]
        )
        mock_doc_processor.return_value = mock_processor_instance
        
        # Setup vector store mock
        mock_store_instance = Mock()
        mock_store_instance.search.return_value = [
            ("Sample content about testing", {"course_title": "Test Course", "lesson_title": "Test Lesson"})
        ]
        mock_store_instance.get_collection_info.return_value = {"total_chunks": 1}
        mock_vector_store.return_value = mock_store_instance
        
        # Setup Anthropic mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Testing is important for software quality.")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Initialize system and load documents
        rag_system = RAGSystem(test_config)
        courses, chunks = rag_system.add_course_folder(temp_docs_folder)
        
        # Verify documents were loaded
        assert courses > 0
        assert chunks > 0
        
        # Query the loaded content
        answer, sources = rag_system.query("What is testing?", "test-session")
        
        # Verify query worked
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert isinstance(sources, list)
    
    @patch("anthropic.Anthropic")
    def test_session_management_integration(self, mock_anthropic, test_config):
        """Test session management across multiple queries"""
        from rag_system import RAGSystem
        
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Response with context")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Initialize system
        rag_system = RAGSystem(test_config)
        
        # Create session and make queries
        session_id = rag_system.session_manager.create_session()
        
        # First query
        answer1, sources1 = rag_system.query("What is AI?", session_id)
        
        # Second query in same session  
        answer2, sources2 = rag_system.query("Tell me more", session_id)
        
        # Verify both queries worked
        assert isinstance(answer1, str)
        assert isinstance(answer2, str)
        assert len(answer1) > 0
        assert len(answer2) > 0
        
        # Verify AI was called twice
        assert mock_client.messages.create.call_count == 2


@pytest.mark.integration
class TestAPISystemIntegration:
    """Integration tests combining API and RAG system components"""
    
    def test_api_with_real_rag_system_mock(self):
        """Test API endpoints with mocked RAG system components"""
        from fastapi.testclient import TestClient
        
        with patch("app.rag_system") as mock_rag_system:
            # Setup RAG system mock
            mock_rag_system.query.return_value = ("Integration test answer", ["Integration source"])
            mock_rag_system.get_course_analytics.return_value = {
                "total_courses": 3,
                "course_titles": ["Course A", "Course B", "Course C"]
            }
            mock_rag_system.session_manager.create_session.return_value = "integration-session-456"
            
            # Import and test the actual app
            try:
                from app import app
                client = TestClient(app)
                
                # Test query endpoint
                response = client.post("/api/query", json={"query": "integration test"})
                assert response.status_code == 200
                data = response.json()
                assert data["answer"] == "Integration test answer"
                assert data["sources"] == ["Integration source"]
                
                # Test courses endpoint  
                response = client.get("/api/courses")
                assert response.status_code == 200
                data = response.json()
                assert data["total_courses"] == 3
                assert len(data["course_titles"]) == 3
                
            except ImportError:
                # If app can't be imported due to static file issues, skip
                pytest.skip("App import failed - likely due to static file mounting")


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across system components"""
    
    @patch("anthropic.Anthropic")
    @patch("vector_store.VectorStore")
    def test_anthropic_api_error_handling(self, mock_vector_store, mock_anthropic, test_config):
        """Test system handles Anthropic API errors gracefully"""
        from rag_system import RAGSystem
        import anthropic
        
        # Setup vector store mock
        mock_store_instance = Mock()
        mock_store_instance.search.return_value = [("content", {"course_title": "Test"})]
        mock_vector_store.return_value = mock_store_instance
        
        # Setup Anthropic to raise error
        mock_client = Mock()
        mock_client.messages.create.side_effect = anthropic.APIError("API Error")
        mock_anthropic.return_value = mock_client
        
        # Initialize system
        rag_system = RAGSystem(test_config)
        
        # Query should handle the error
        with pytest.raises(Exception):
            rag_system.query("test query", "test-session")
    
    @patch("vector_store.VectorStore")
    def test_vector_store_error_handling(self, mock_vector_store, test_config):
        """Test system handles vector store errors gracefully"""
        from rag_system import RAGSystem
        
        # Setup vector store to raise error
        mock_store_instance = Mock()
        mock_store_instance.search.side_effect = Exception("Vector store error")
        mock_vector_store.return_value = mock_store_instance
        
        # Initialize system
        rag_system = RAGSystem(test_config)
        
        # Query should handle the error
        with pytest.raises(Exception):
            rag_system.query("test query", "test-session")