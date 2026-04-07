import pytest
import json
import hashlib
from unittest.mock import MagicMock, patch, mock_open, AsyncMock
from pathlib import Path
from crawler.crawler import Crawler, CrawlerConfig

@pytest.fixture
def mock_crawler():
    config = CrawlerConfig(
        site="javdb",
        media_dir="/tmp/media_detail",
        actress_dir="/tmp/actress",
        ain_list_file="tests/mock_ain_list.json"
    )
    # Mocking environment/config loading to avoid real file I/O during init
    with patch("crawler.crawler.SITES_CONFIG", {"javdb": {"url_template": "test/{scene_name}", "home_url": "test/"}}):
        crawler = Crawler(config)
        return crawler

def test_inject_meta_stable_hash(mock_crawler):
    data = {"id": "ABC-123", "title": "Test Title", "performers": ["Actor A"]}
    
    # First injection
    result1 = mock_crawler._inject_meta(data.copy())
    hash1 = result1["_meta"]["hash"]
    
    # Second injection with same data
    result2 = mock_crawler._inject_meta(data.copy())
    hash2 = result2["_meta"]["hash"]
    
    assert hash1 == hash2
    assert "scraped_at" in result1["_meta"]
    
    # Injection with different order should still have same hash (due to sort_keys=True)
    data_reordered = {"title": "Test Title", "performers": ["Actor A"], "id": "ABC-123"}
    result3 = mock_crawler._inject_meta(data_reordered)
    assert result3["_meta"]["hash"] == hash1

def test_stash_cache_memoization(mock_crawler):
    # Mock the underlying stash request
    mock_crawler._stash_request = MagicMock(return_value={"findPerformers": {"performers": [{"id": "123", "name": "Actor A"}]}})
    
    # First call: should hit the request
    pid1 = mock_crawler._get_or_create_performer("Actor A")
    assert pid1 == "123"
    assert mock_crawler._stash_request.call_count == 1
    
    # Second call: should hit the cache
    pid2 = mock_crawler._get_or_create_performer("Actor A")
    assert pid2 == "123"
    assert mock_crawler._stash_request.call_count == 1 # Still 1

@patch("crawler.crawler.requests.post")
def test_sync_to_stash_idempotency_skip(mock_post, mock_crawler):
    # Setup mock data with matching hashes
    scene_id = "TEST-999"
    mock_hash = "abcde12345"
    detail_json = {
        "_meta": {
            "hash": mock_hash,
            "last_synced_hash": mock_hash
        },
        "id": scene_id
    }
    
    # Mock file existence and content
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(detail_json))):
        
        # We need to mock media_list retrieval
        mock_crawler.actress_dir = Path("/tmp/actress")
        mock_crawler.media_dir = Path("/tmp/media_detail")
        
        # Manually invoke a sync for one item
        # We bypass the full sync_to_stash_group to target the loop logic if needed, 
        # or just mock the dependencies of sync_to_stash_group.
        
        with patch.object(mock_crawler, "_find_scene_by_volume") as mock_find:
            # If skipping works, _find_scene_by_volume should NEVER be called
            media_list = [{"id": scene_id}]
            
            # Since sync_to_stash_group is async, we use a small helper or run it
            import asyncio
            
            async def run_test():
                # Mock loading media_list.json
                with patch("builtins.open", mock_open(read_data=json.dumps(media_list))):
                    await mock_crawler.sync_to_stash_group("ActorName")
            
            asyncio.run(run_test())
            
            assert mock_find.call_count == 0

@pytest.mark.asyncio
async def test_get_client_session_type(mock_crawler):
    headers = {"User-Agent": "Test"}
    
    # Case 1: ain_list_file is set (should be CachedSession if available)
    with patch("crawler.crawler.CachedSession", AsyncMock) as mock_cached, \
         patch("crawler.crawler.SQLiteBackend", MagicMock()) as mock_sqlite:
        session = mock_crawler._get_client_session(headers)
        assert session is not None
        # mock_cached is the class here, so session is an instance of AsyncMock
        await session.close()

    # Case 2: No ain_list_file (should be standard session)
    mock_crawler.config.ain_list_file = None
    import aiohttp
    session = mock_crawler._get_client_session(headers)
    assert isinstance(session, aiohttp.ClientSession)
    await session.close()
