# 校验方案令牌并创建异步生图任务；费用扣减由创建领域事件在同一事务中完成。

> 入参 `designType=2`（Room）

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/space/generation-tasks

所属模块: Spaces

## 请求体

```json
{
  "designType": 0,
  "proposalToken": "string"
}
```

字段说明：

- `designType`: int, 可选
- `proposalToken`: string, 可选

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": {
    "taskId": "string",
    "status": 0,
    "generationCost": 0
  }
}
```

**401**: Unauthorized

**403**: Forbidden
