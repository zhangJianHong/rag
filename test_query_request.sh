#!/bin/bash
curl -X POST http://localhost:8800/api/query/v2 \
  -H "Content-Type: application/json" \
  -d '{"query":"语音识别和人物识别","namespace":"technology_competition","retrieval_mode":"auto","retrieval_method":"hybrid","namespaces":null,"top_k":10,"alpha":0.5,"similarity_threshold":0,"session_id":"9cbeea05-b392-4169-a53c-62c5bd5a63f8"}'
