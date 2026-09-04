import asyncio
import threading


def test_run_scan_is_offloaded_from_event_loop(monkeypatch):
    """The background scanner must not execute blocking scan work on the event-loop thread."""
    import app.main as main

    event_loop_thread = threading.get_ident()
    scan_thread = None
    scan_started = threading.Event()
    release_scan = threading.Event()

    def fake_run_scan():
        nonlocal scan_thread
        scan_thread = threading.get_ident()
        scan_started.set()
        release_scan.wait(timeout=2)
        return {"found": 0, "added": 0, "updated": 0, "duplicates": 0}

    monkeypatch.setattr(main, "_run_scan", fake_run_scan)
    monkeypatch.setattr(main, "SCAN_INTERVAL_SECONDS", 999999)

    async def exercise():
        task = asyncio.create_task(main._background_scan_loop())
        try:
            # If _run_scan is executed directly on the event loop, this timeout
            # cannot complete while fake_run_scan is waiting.
            started = await asyncio.to_thread(scan_started.wait, 1)
            assert started is True
            assert scan_thread != event_loop_thread
        finally:
            release_scan.set()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    asyncio.run(exercise())
