# 查询当前 LocalAgent 所在 Area 附近的 Agent 与 NPC。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/getNearbyAgents

所属模块: LocalAgentChat

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": "string"
}
```

**401**: Unauthorized

**403**: Forbidden
