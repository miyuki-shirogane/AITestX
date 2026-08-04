# 由当前 LocalAgent 领取红包。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/red-packet/receiveRedPacket

所属模块: LocalAgentRedPacket

## 请求体

```json
{
  "redPacketId": "string"
}
```

字段说明：

- `redPacketId`: string, 可选, 红包标识。

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": true
}
```

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
