# 分页查询用户与AI搭档聊天消息

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/chat/messages/search

所属模块: UserAgentChat

## 请求体

```json
{
  "pageIndex": 0,
  "pageSize": 0,
  "startTime": "string",
  "endTime": "string",
  "keyword": "string"
}
```

字段说明：

- `pageIndex`: int, 可选, 当前页码，从1开始
- `pageSize`: int, 可选, 每页数量
- `startTime`: string, 可选, 起始日期，不传默认7天前
- `endTime`: string, 可选, 结束日期，不传默认当前日期
- `keyword`: string, 可选, 聊天内容关键字

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
