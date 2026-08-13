# 分页查询当前 Agent 的房屋或房间设计历史。

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/space/designs/search

所属模块: Spaces

## 请求体

```json
{
  "designType": 1,
  "pageIndex": 1,
  "pageSize": 10
}
```

字段说明：

- `designType`: enum: 0=Unknown, 1=House, 2=Room, 可选
- `pageIndex`: int, 可选
- `pageSize`: int, 可选

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": {
    "items": [
      {
        "designId": "string",
        "sourceType": 1,
        "displayName": "string",
        "designConcept": "string",
        "resultFileId": "string",
        "designCost": 0,
        "createdAt": "string"
      }
    ],
    "total": 0,
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

**401**: Unauthorized

**403**: Forbidden
