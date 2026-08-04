# 流式发送用户与AI搭档聊天消息

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/chat/message/stream

所属模块: UserAgentChat

## 请求体

```json
{
  "threadId": "string",
  "content": "string"
}
```

字段说明：

- `threadId`: string, 必填, 聊天线程ID
- `content`: string, 必填, 消息内容

## 响应

**204**: No Content

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
