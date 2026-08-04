# 上传文件

POST https://solgrid-friend-api.rivtower.cc/api/v1/file/upload

所属模块: File

## 请求体

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

**401**: Unauthorized

**403**: Forbidden
