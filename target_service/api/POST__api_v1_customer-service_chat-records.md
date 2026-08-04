# 查询客服对话记录

POST https://solgrid-friend-api.rivtower.cc/api/v1/customer-service/chat-records

所属模块: CustomerService

## 请求体

```json
{
  "conversationId": "string"
}
```

字段说明：

- `conversationId`: string, 可选, 会话 ID

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": []
}
```

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
