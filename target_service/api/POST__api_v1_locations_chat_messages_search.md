# 分页查询场景聊天室消息

POST https://solgrid-friend-api.rivtower.cc/api/v1/locations/chat/messages/search

所属模块: Locations

## 请求体

```json
{
  "locationId": "string",
  "scope": "string",
  "pageIndex": 0,
  "pageSize": 0,
  "startTime": "string",
  "endTime": "string"
}
```

字段说明：

- `locationId`: string, 必填, 地点 ID
- `scope`: object, 可选, 查询范围
- `pageIndex`: int, 可选, 当前页码，从1开始
- `pageSize`: int, 可选, 每页数量
- `startTime`: string, 可选, 起始时间，不传默认7天前
- `endTime`: string, 可选, 结束时间，不传默认当前时间

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
