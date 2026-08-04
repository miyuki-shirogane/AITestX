# 下载文件

GET https://solgrid-friend-api.rivtower.cc/api/v1/file/download

所属模块: File

## 请求参数

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| fileId | query | string | 是 | 文件 Id |
| fileType | query | object | 是 | 文件类型 |
| autoDownload | query | boolean | 是 | 是否自动下载 |

## 响应

**200**: Success
```json
{}
```

**401**: Unauthorized

**403**: Forbidden
