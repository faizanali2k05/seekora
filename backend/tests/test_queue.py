import pytest

from app.crawler.queue import MemoryCrawlQueue


@pytest.mark.asyncio
async def test_crawl_job_lifecycle() -> None:
    queue = MemoryCrawlQueue()
    queued = await queue.enqueue("https://example.com/")
    assert queued.status == "queued"

    running = await queue.dequeue(wait_seconds=1)
    assert running is not None
    assert running.status == "running"

    await queue.update(running, status="complete", document_id="doc-1")
    complete = await queue.get(running.id)
    assert complete is not None
    assert complete.status == "complete"
    assert complete.document_id == "doc-1"
