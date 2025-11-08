"""
LLM服务 - 处理与大语言模型的交互
支持多个提供商动态初始化
"""
import os
import json
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from openai import AsyncOpenAI
import anthropic
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config.settings import get_settings
from app.models.chat import ChatMessage
from app.models.llm_models import LLMModel

settings = get_settings()

class LLMService:
    """LLM服务类 - 支持多模型动态初始化"""

    def __init__(self, db: Session = None):
        """初始化LLM服务"""
        self.db = db
        # 缓存客户端，避免重复创建
        self._clients = {}
        self.default_model = "gpt-3.5-turbo"

    def _get_client_for_model(self, model_name: str) -> tuple:
        """
        根据模型名称获取对应的客户端

        Returns:
            tuple: (client, model_name, provider)
        """
        # 如果有数据库配置，优先从数据库获取
        if self.db:
            model_config = self.db.execute(
                select(LLMModel).where(LLMModel.name == model_name, LLMModel.is_active == True)
            ).scalar_one_or_none()

            if model_config:
                provider = model_config.provider
                actual_model_name = model_config.model_name
                api_key = model_config.api_key or os.getenv(f"{provider.upper()}_API_KEY")
                base_url = model_config.base_url

                # 生成客户端缓存键
                cache_key = f"{provider}:{model_name}"

                if cache_key not in self._clients:
                    if provider.lower() == "openai":
                        client = AsyncOpenAI(
                            api_key=api_key,
                            base_url=base_url or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
                        )
                    elif provider.lower() == "anthropic":
                        client = anthropic.Anthropic(
                            api_key=api_key,
                            base_url=base_url or os.getenv("ANTHROPIC_API_BASE", "https://api.anthropic.com/v1")
                        )
                    else:
                        # 为其他提供商预留扩展
                        client = AsyncOpenAI(
                            api_key=api_key,
                            base_url=base_url
                        )

                    self._clients[cache_key] = client

                return self._clients[cache_key], actual_model_name, provider

        # 默认回退到环境变量配置
        cache_key = f"openai:{model_name}"
        if cache_key not in self._clients:
            self._clients[cache_key] = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            )

        return self._clients[cache_key], model_name, "openai"

    async def get_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        获取LLM响应（非流式）
        """
        try:
            # 获取模型对应的客户端
            model_name = model or self.default_model
            client, actual_model, provider = self._get_client_for_model(model_name)

            # 调用对应提供商的API
            if provider.lower() == "openai":
                response = await client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                return {
                    "content": response.choices[0].message.content,
                    "tokens_used": response.usage.total_tokens,
                    "model": response.model
                }
            else:
                # 为其他提供商预留扩展
                raise ValueError(f"不支持的提供商: {provider}")

        except Exception as e:
            print(f"LLM completion error: {e}")
            raise

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        session_id: str = None,
        db = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成LLM响应
        """
        try:
            # 获取模型对应的客户端
            model_name = model or self.default_model
            client, actual_model, provider = self._get_client_for_model(model_name)

            # 调用对应提供商的API
            if provider.lower() == "openai":
                stream = await client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
            elif provider.lower() == "anthropic":
                message = client.messages.create(
                    model=actual_model,
                    max_tokens=max_tokens,
                    #system="You are a helpful assistant.",
                    messages= messages,
                    temperature=temperature,
                    stream=False
                )

            else:
                 # 为其他提供商预留扩展
                 # 默认使用OpenAI的流式接口
                stream = await client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                # raise ValueError(f"不支持的提供商: {provider}")

            full_response = ""
            if provider.lower() == "openai":
                  async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        # 发送SSE格式的数据
                        yield f"data: {json.dumps({'content': content, 'type': 'content'})}\n\n"


            elif provider.lower() == "anthropic":
                for block in message.content:
                    if block.type == "thinking":
                        full_response += block.thinking
                        yield f"data: {json.dumps({'content': block.thinking, 'type': 'thinking'})}\n\n"
                    elif block.type == "text":
                        full_response += block.text
                        # 发送SSE格式的数据
                        yield f"data: {json.dumps({'content': block.text, 'type': 'content'})}\n\n"
            else:
                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        # 发送SSE格式的数据
                        yield f"data: {json.dumps({'content': content, 'type': 'content'})}\n\n"

            # 保存完整响应到数据库
            if session_id and db:
                assistant_message = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    metadata={
                        "model": model_name,
                        "temperature": temperature
                    }
                )
                db.add(assistant_message)
                db.commit()

            # 发送结束信号
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            print(f"Stream completion error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    async def get_embeddings(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """
        获取文本的向量嵌入
        """
        try:
            # 获取默认的OpenAI客户端
            client, _, _ = self._get_client_for_model("gpt-3.5-turbo")
            response = await client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embeddings error: {e}")
            raise

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        简单估算：平均每4个字符约等于1个token
        """
        return len(text) // 4

    async def summarize_text(self, text: str, max_length: int = 100) -> str:
        """
        文本摘要生成
        """
        messages = [
            {"role": "system", "content": "你是一个专业的文本摘要助手。"},
            {"role": "user", "content": f"请将以下文本总结为不超过{max_length}字的摘要：\n\n{text}"}
        ]

        response = await self.get_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=max_length * 2
        )

        return response["content"]

    async def generate_session_title(self, first_message: str) -> str:
        """
        根据第一条消息生成会话标题
        """
        messages = [
            {"role": "system", "content": "根据用户的第一条消息，生成一个简短的对话标题（不超过20字）。"},
            {"role": "user", "content": first_message}
        ]

        response = await self.get_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=50
        )

        return response["content"][:50]  # 确保不超过50字符