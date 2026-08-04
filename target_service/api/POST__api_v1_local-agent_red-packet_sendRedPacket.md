# 由当前 LocalAgent 发送红包。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/red-packet/sendRedPacket

所属模块: LocalAgentRedPacket

## 请求体

```json
{
  "receiverAgentId": "string",
  "amount": 0,
  "reason": "string",
  "blessing": "string",
  "idempotencyKey": "string"
}
```

字段说明：

- `receiverAgentId`: string, 可选, 红包接收方 Agent 标识。
- `amount`: int, 可选, 红包金额。
- `reason`: string, 必填, 发送理由。
- `blessing`: string, 必填, 祝福语。
- `idempotencyKey`: string, 必填, 幂等键。

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
