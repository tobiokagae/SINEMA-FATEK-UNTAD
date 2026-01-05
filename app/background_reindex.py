# -*- coding: utf-8 -*-
"""Background Reindex Service with Debounce Mechanism

This module provides a debounced background reindexing service.
When files are deleted, the reindex is scheduled to run after a delay.
If more deletes happen before the delay expires, the timer resets.
This ensures reindex only runs once after all deletes are complete.
"""

import threading
import time
from typing import Optional, Callable
from flask import Flask


class BackgroundReindexService:
    """Service for managing debounced background reindexing"""
    
    _instance: Optional['BackgroundReindexService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._timer: Optional[threading.Timer] = None
        self._reindex_lock = threading.Lock()
        self._is_reindexing = False
        self._pending_reindex = False
        self._delay_seconds = 5.0  # Wait 5 seconds after last delete
        self._app: Optional[Flask] = None
        self._reindex_callback: Optional[Callable] = None
        self._initialized = True
    
    def init_app(self, app: Flask, reindex_callback: Callable):
        """Initialize with Flask app and reindex callback function"""
        self._app = app
        self._reindex_callback = reindex_callback
        app.logger.info("BackgroundReindexService initialized with 5s debounce")
    
    def schedule_reindex(self):
        """Schedule a reindex with debounce - cancels any pending reindex and starts new timer"""
        with self._reindex_lock:
            # Cancel existing timer if any
            if self._timer is not None:
                self._timer.cancel()
                if self._app:
                    self._app.logger.debug("Cancelled pending reindex timer")
            
            # If currently reindexing, mark as pending
            if self._is_reindexing:
                self._pending_reindex = True
                if self._app:
                    self._app.logger.info("Reindex in progress, marking pending reindex")
                return
            
            # Start new timer
            self._timer = threading.Timer(self._delay_seconds, self._execute_reindex)
            self._timer.daemon = True
            self._timer.start()
            
            if self._app:
                self._app.logger.info(f"Scheduled reindex in {self._delay_seconds}s")
    
    def _execute_reindex(self):
        """Execute the actual reindex operation"""
        with self._reindex_lock:
            if self._is_reindexing:
                self._pending_reindex = True
                return
            self._is_reindexing = True
            self._pending_reindex = False
        
        try:
            if self._app:
                self._app.logger.info("Starting background reindex...")
            
            if self._reindex_callback:
                # Run reindex in app context
                if self._app:
                    with self._app.app_context():
                        self._reindex_callback()
                else:
                    self._reindex_callback()
            
            if self._app:
                self._app.logger.info("Background reindex completed successfully")
                
        except Exception as e:
            if self._app:
                self._app.logger.error(f"Background reindex failed: {e}")
        finally:
            with self._reindex_lock:
                self._is_reindexing = False
                
                # If there's a pending reindex, schedule it
                if self._pending_reindex:
                    self._pending_reindex = False
                    if self._app:
                        self._app.logger.info("Processing pending reindex request")
                    self._timer = threading.Timer(1.0, self._execute_reindex)
                    self._timer.daemon = True
                    self._timer.start()
    
    @property
    def is_reindexing(self) -> bool:
        """Check if reindex is currently running"""
        return self._is_reindexing
    
    @property
    def has_pending(self) -> bool:
        """Check if there's a pending reindex"""
        return self._pending_reindex or (self._timer is not None and self._timer.is_alive())


# Global instance
background_reindex_service = BackgroundReindexService()


def get_background_reindex_service() -> BackgroundReindexService:
    """Get the singleton instance of BackgroundReindexService"""
    return background_reindex_service
