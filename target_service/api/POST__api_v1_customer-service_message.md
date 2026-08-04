# 发送客服消息

POST https://solgrid-friend-api.rivtower.cc/api/v1/customer-service/message

所属模块: CustomerService

## 请求体

```json
{
  "customerServiceAgentId": "string",
  "conversationId": "string",
  "content": "string"
}
```

字段说明：

- `customerServiceAgentId`: string, 可选, 客服 Agent ID，不传则使用第一个启用的客服 Agent
- `conversationId`: string, 可选, 会话 ID，不传则新建会话
- `content`: string, 必填, 消息内容

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
