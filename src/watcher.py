import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio
from src.config import PDF_DIR, log_stderr

class PDFHandler(FileSystemEventHandler):
    def __init__(self, pipeline):
        self.pipeline = pipeline
        
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.pdf'):
            log_stderr(f"New PDF detected: {event.src_path}")
            # Trigger ingestion for the specific file's directory to be efficient
            # In a fully async system, we'd use an async task queue. 
            # For simplicity, we call the sync ingest method here.
            self.pipeline.ingest(base_path=Path(event.src_path).parent)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.pdf'):
            log_stderr(f"PDF modified: {event.src_path}")
            self.pipeline.ingest(base_path=Path(event.src_path).parent, force=True)

async def start_watcher(pipeline):
    path = str(PDF_DIR)
    # Ensure directory exists before watching
    Path(path).mkdir(parents=True, exist_ok=True)
    
    event_handler = PDFHandler(pipeline)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    log_stderr(f"Started watching {path} for PDF changes...")
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        observer.stop()
        log_stderr("Watcher stopped.")
    observer.join()