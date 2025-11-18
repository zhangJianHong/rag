"""
WebSocket 路由
提供实时数据推送功能
"""
import json
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.middleware.auth import get_current_user_websocket
from app.models.database import User

router = APIRouter()
logger = logging.getLogger(__name__)

# 存储活跃的WebSocket连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[WebSocket, str] = {}  # WebSocket -> user_id

    async def connect(self, websocket: WebSocket, user_id: str, endpoint: str):
        await websocket.accept()

        if endpoint not in self.active_connections:
            self.active_connections[endpoint] = []

        self.active_connections[endpoint].append(websocket)
        self.user_connections[websocket] = user_id

        logger.info(f"用户 {user_id} 连接到 WebSocket 端点: {endpoint}")
        logger.info(f"当前活跃连接数: {len(self.active_connections.get(endpoint, []))}")

    def disconnect(self, websocket: WebSocket, endpoint: str):
        if endpoint in self.active_connections:
            self.active_connections[endpoint].remove(websocket)

        user_id = self.user_connections.pop(websocket, None)

        logger.info(f"用户 {user_id} 断开 WebSocket 连接: {endpoint}")
        logger.info(f"当前活跃连接数: {len(self.active_connections.get(endpoint, []))}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")

    async def broadcast(self, message: dict, endpoint: str):
        if endpoint not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[endpoint]:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection, endpoint)

    async def broadcast_to_user(self, message: dict, user_id: str, endpoint: str):
        if endpoint not in self.active_connections:
            return

        for connection in self.active_connections[endpoint]:
            if self.user_connections.get(connection) == user_id:
                try:
                    await connection.send_text(json.dumps(message, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"向用户 {user_id} 发送消息失败: {e}")
                    self.disconnect(connection, endpoint)

manager = ConnectionManager()

@router.websocket("/ws/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    Dashboard 实时数据推送 WebSocket
    """
    # 认证用户
    try:
        # 从查询参数或头部获取token
        token = None
        if "authorization" in websocket.headers:
            token = websocket.headers["authorization"].replace("Bearer ", "")
        elif "token" in websocket.query_params:
            token = websocket.query_params["token"]

        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return

        # 验证token并获取用户
        current_user = await get_current_user_websocket(token, db)
        user_id = str(current_user.id)

    except Exception as e:
        logger.error(f"WebSocket认证失败: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await manager.connect(websocket, user_id, "dashboard")

    try:
        # 发送初始连接成功消息
        await manager.send_personal_message({
            "type": "connection_established",
            "message": "WebSocket连接已建立",
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # 保持连接并处理消息
        while True:
            try:
                # 接收客户端消息（如果有）
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理客户端发送的消息
                await handle_client_message(message, websocket, user_id, db)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"处理WebSocket消息时出错: {e}")
                # 发送错误消息但不关闭连接
                await manager.send_personal_message({
                    "type": "error",
                    "message": "处理消息时出错",
                    "timestamp": datetime.now().isoformat()
                }, websocket)

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, "dashboard")

async def handle_client_message(message: dict, websocket: WebSocket, user_id: str, db: Session):
    """
    处理客户端发送的WebSocket消息
    """
    message_type = message.get("type")

    if message_type == "ping":
        # 心跳检测
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }, websocket)

    elif message_type == "subscribe_stats":
        # 订阅统计数据更新
        await manager.send_personal_message({
            "type": "subscription_confirmed",
            "subscription": "stats_update",
            "timestamp": datetime.now().isoformat()
        }, websocket)

    elif message_type == "get_stats":
        # 获取当前统计数据
        from app.routers.dashboard import get_dashboard_stats
        try:
            # 这里需要手动创建用户依赖
            from app.models.database import User
            current_user = db.query(User).filter(User.id == int(user_id)).first()
            if not current_user:
                raise HTTPException(status_code=404, detail="用户不存在")

            stats = await get_dashboard_stats(db, current_user)

            await manager.send_personal_message({
                "type": "stats_update",
                "data": stats,
                "timestamp": datetime.now().isoformat()
            }, websocket)

        except Exception as e:
            logger.error(f"获取统计数据失败: {e}")
            await manager.send_personal_message({
                "type": "error",
                "message": "获取统计数据失败",
                "timestamp": datetime.now().isoformat()
            }, websocket)

# 以下函数可以被其他地方调用来推送实时数据
async def broadcast_stats_update(stats_data: dict):
    """
    广播统计数据更新到所有连接的dashboard客户端
    """
    await manager.broadcast({
        "type": "stats_update",
        "data": stats_data,
        "timestamp": datetime.now().isoformat()
    }, "dashboard")

async def broadcast_document_uploaded(document_data: dict):
    """
    广播文档上传通知
    """
    await manager.broadcast({
        "type": "document_uploaded",
        "data": document_data,
        "timestamp": datetime.now().isoformat()
    }, "dashboard")

async def broadcast_new_query(query_data: dict):
    """
    广播新查询通知
    """
    await manager.broadcast({
        "type": "new_query",
        "data": query_data,
        "timestamp": datetime.now().isoformat()
    }, "dashboard")

async def broadcast_system_notification(notification: dict):
    """
    广播系统通知
    """
    await manager.broadcast({
        "type": "system_notification",
        "data": notification,
        "timestamp": datetime.now().isoformat()
    }, "dashboard")

# 导出manager供其他模块使用
__all__ = [
    "manager",
    "broadcast_stats_update",
    "broadcast_document_uploaded",
    "broadcast_new_query",
    "broadcast_system_notification"
]