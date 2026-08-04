# 检查当前 LocalAgent 的红包发送记忆。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/red-packet/checkAgentRedPacketMemory

所属模块: LocalAgentRedPacket

## 请求体

```json
{
  "receiverAgentId": "string",
  "reason": "string"
}
```

字段说明：

- `receiverAgentId`: string, 可选, 红包接收方 Agent 标识。
- `reason`: string, 必填, 计划发送红包的理由。

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

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
