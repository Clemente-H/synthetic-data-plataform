#!/usr/bin/env python3
"""
WebSocket API - Real-time communication for pipeline progress
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import logging
import json
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Connection manager for WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_tasks: Dict[str, str] = {}  # client_id -> task_id mapping
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"🔌 WebSocket client {client_id} connected")
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_tasks:
            del self.client_tasks[client_id]
        logger.info(f"🔌 WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_task_update(self, task_id: str, message: dict):
        """Send message to all clients watching this task"""
        disconnected_clients = []
        for client_id, client_task_id in self.client_tasks.items():
            if client_task_id == task_id:
                try:
                    await self.send_personal_message(message, client_id)
                except:
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time pipeline updates
    """
    await manager.connect(websocket, client_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "message": "Connected to Synthetic Data Platform",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }, client_id)
        
        while True:
            # Listen for client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe_task":
                task_id = message.get("task_id")
                manager.client_tasks[client_id] = task_id
                await manager.send_personal_message({
                    "type": "subscribed",
                    "task_id": task_id,
                    "message": f"Subscribed to task {task_id}"
                }, client_id)
                
            elif message.get("type") == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)

# Helper functions for sending updates from other parts of the application
async def send_pipeline_update(task_id: str, stage: str, progress: float, message: str, data: dict = None):
    """Send pipeline progress update to subscribed clients"""
    update = {
        "type": "pipeline_progress",
        "task_id": task_id,
        "stage": stage,
        "progress": progress,  # 0.0 to 1.0
        "message": message,
        "data": data or {},
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_task_update(task_id, update)

async def send_pipeline_error(task_id: str, stage: str, error: str):
    """Send pipeline error to subscribed clients"""
    update = {
        "type": "pipeline_error",
        "task_id": task_id,
        "stage": stage,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_task_update(task_id, update)

async def send_pipeline_complete(task_id: str, results: dict):
    """Send pipeline completion to subscribed clients"""
    update = {
        "type": "pipeline_complete", 
        "task_id": task_id,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_task_update(task_id, update)

async def send_sample_generated(task_id: str, sample: dict, total_generated: int, total_expected: int):
    """Send individual sample as it's generated"""
    update = {
        "type": "sample_generated",
        "task_id": task_id,
        "sample": sample,
        "progress": {
            "generated": total_generated,
            "expected": total_expected,
            "percentage": (total_generated / total_expected) * 100 if total_expected > 0 else 0
        },
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_task_update(task_id, update)

# Export the manager for use in other modules
__all__ = ['router', 'manager', 'send_pipeline_update', 'send_pipeline_error', 'send_pipeline_complete', 'send_sample_generated']