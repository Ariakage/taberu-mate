# 用户注册与登录流程

## 数据模型

用户数据保存在 SQLite 的 `users` 表中：

- `id`: UUID 字符串，服务端注册时生成，不使用数据库自增。
- `username`: 用户名，3 到 32 位，只允许英文字母、数字和下划线，大小写不重复。
- `nickname`: 昵称，1 到 50 位，可包含中文等展示字符；注册时不传则默认等于 `username`。
- `avatar_url`: 头像 URL，可为空，注册时由 Pydantic 校验为 URL。
- `password_salt`: 每位用户独立生成的 Argon2id salt。
- `password_hash`: Argon2id PHC 字符串，只保存哈希结果，不保存原始密码。
- `created_at` / `updated_at`: ISO 8601 时间。

登录令牌签名密钥从 `.env` 读取，不与密码哈希 salt 复用：

```env
TABERU_MATE_AUTH_TOKEN_SECRET="replace-with-a-long-random-token-secret"
```

> 当前实现使用 Argon2id，并为每位用户保存独立 salt。

## Token 与会话模型

当前认证使用短时 Access Token + 长时 Refresh Token：

- Access Token: JWT 格式，默认 15 分钟过期，包含 `sub`、`typ=access`、`jti`、`iat`、`exp`。
- Refresh Token: JWT 格式，默认 30 天过期，包含 `sub`、`typ=refresh`、`jti`、`iat`、`exp`。
- Refresh Token 必须存服务端：数据库 `refresh_tokens` 表保存 refresh token 的 HMAC-SHA256 哈希、`jti`、用户 id、过期时间、撤销时间、替换后的 `jti`、User-Agent 和 IP。
- Access Token 可撤销：数据库 `access_token_revocations` 表保存已撤销 access token 的 `jti`，登出后旧 access token 会立即失效。
- 登录和刷新都会生成新的 `jti` 与新签名，避免会话固定攻击。

如果通过 Cookie 使用 token，服务端会设置：

- `access_token`: `HttpOnly`、`Secure`、`SameSite=Strict`
- `refresh_token`: `HttpOnly`、`Secure`、`SameSite=Strict`
- `csrf_token`: `Secure`、`SameSite=Strict`，非 `HttpOnly`，用于双重提交 CSRF 校验

Access Token 同时会在登录/刷新响应体中返回，方便非浏览器客户端使用 `Authorization: Bearer <access_token>`。

## CSRF 流程

所有非 GET 的认证状态变更接口都需要双重提交 CSRF Token：

1. 客户端先调用 `GET /api/v1/auth/csrf`。
2. 服务端返回 `csrf_token`，并设置同名 `csrf_token` Cookie。
3. 客户端调用 `POST /api/v1/auth/register`、`POST /api/v1/auth/login`、`POST /api/v1/auth/refresh`、`POST /api/v1/auth/logout` 时，必须同时带上：

```http
Cookie: csrf_token=<csrf_token>
X-CSRF-Token: <csrf_token>
```

Cookie 和 Header 不一致或缺失时，服务端返回 `403`。

## 注册流程

接口：`POST /api/v1/auth/register`

请求头：

```http
X-CSRF-Token: <csrf_token>
```

请求体：

```json
{
  "username": "ariakage",
  "nickname": "Ariakage",
  "avatar_url": "https://example.com/avatar.png",
  "password": "strong-password"
}
```

服务端流程：

1. Pydantic 校验用户名、昵称、头像 URL 和密码长度。
2. 查询用户名是否已存在，查询使用 SQL 参数绑定。
3. 生成 UUID 作为用户 id。
4. 为该用户生成独立随机 salt。
5. 使用 Argon2id 计算密码哈希，哈希以 PHC 格式存储。
6. 使用参数化 SQL 写入用户记录。
7. 返回公开用户信息，不返回原始密码或密码哈希。

成功响应：

```json
{
  "id": "uuid",
  "username": "ariakage",
  "nickname": "Ariakage",
  "avatar_url": "https://example.com/avatar.png",
  "created_at": "2026-06-21T00:00:00+00:00"
}
```

## 登录流程

接口：`POST /api/v1/auth/login`

请求头：

```http
X-CSRF-Token: <csrf_token>
```

请求体：

```json
{
  "username": "ariakage",
  "password": "strong-password"
}
```

服务端流程：

1. Pydantic 校验用户名和密码长度。
2. 使用参数化 SQL 按用户名查询用户。
3. 使用该用户自己的 `password_salt` 和 Argon2id PHC 哈希验证密码。
4. 登录成功后生成全新的 Access Token 和 Refresh Token，二者都有新的 `jti` 和签名。
5. Refresh Token 的哈希写入数据库，原文只通过响应 Cookie 发给客户端。
6. 设置安全 Cookie，并返回 Access Token、过期时间、新的 CSRF Token 和公开用户信息。
7. 用户名不存在或密码错误时统一返回 `401`，避免泄露用户是否存在。

成功响应：

```json
{
  "access_token": "signed-token",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_expires_in": 2592000,
  "csrf_token": "new-csrf-token",
  "user": {
    "id": "uuid",
    "username": "ariakage",
    "nickname": "Ariakage",
    "avatar_url": "https://example.com/avatar.png",
    "created_at": "2026-06-21T00:00:00+00:00"
  }
}
```

响应 Cookie：

```http
Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=strict
Set-Cookie: refresh_token=<jwt>; HttpOnly; Secure; SameSite=strict
Set-Cookie: csrf_token=<csrf>; Secure; SameSite=strict
```

## 刷新流程

接口：`POST /api/v1/auth/refresh`

请求头：

```http
X-CSRF-Token: <csrf_token>
```

请求 Cookie：

```http
Cookie: refresh_token=<refresh_jwt>; csrf_token=<csrf_token>
```

服务端流程：

1. 校验 CSRF Cookie 与 Header。
2. 校验 Refresh Token 签名、类型、过期时间和 `jti`。
3. 按 `jti` 查询数据库中的 refresh token 记录。
4. 比对请求中的 refresh token 哈希与数据库哈希。
5. 如果记录不存在、已撤销、已过期或哈希不一致，返回 `401` 并记录安全事件。
6. 生成新的 Access Token 与 Refresh Token。
7. 将旧 Refresh Token 标记为撤销，并记录 `replaced_by_jti`。
8. 写入新 Refresh Token 哈希，设置新的 Cookie 和 CSRF Token。

## 登出与撤销流程

接口：`POST /api/v1/auth/logout`

请求头：

```http
Authorization: Bearer <access_token>
X-CSRF-Token: <csrf_token>
```

请求 Cookie：

```http
Cookie: refresh_token=<refresh_jwt>; csrf_token=<csrf_token>
```

服务端流程：

1. 校验 CSRF Cookie 与 Header。
2. 如果请求中有 Access Token，解析其 `jti` 并写入 `access_token_revocations`。
3. 如果请求中有 Refresh Token，解析其 `jti` 并将数据库记录标记为撤销。
4. 清除 `access_token`、`refresh_token` 和 `csrf_token` Cookie。
5. 返回 `204`。

## 获取当前用户

接口：`GET /api/v1/users/me`

请求头：

```http
Authorization: Bearer <access_token>
```

也可以通过 `access_token` Cookie 访问。服务端会校验 Access Token 签名、类型、过期时间、`jti` 是否已撤销，然后根据 token 中的用户 UUID 查询用户。

## 注入与攻击防护

- SQL 注入：所有数据库读写都使用 `?` 参数绑定，不拼接用户输入。
- 用户名注入：用户名只允许英文字母、数字、下划线，拒绝空格、引号、分号等字符。
- 昵称注入：昵称只作为展示字段保存和返回，不参与 SQL 拼接；前端渲染时仍应使用框架默认转义，避免把昵称当作 HTML 注入页面。
- 重复注册：数据库使用 `lower(username)` 唯一索引，并在插入时捕获唯一约束冲突。
- 密码泄露：接口响应不返回 `password_salt` 或 `password_hash`，数据库不保存原始密码。
- 密码破解防护：新密码使用 Argon2id，并为每位用户生成独立 salt；相同密码在不同用户之间也会得到不同哈希。
- Token 篡改：Access Token 和 Refresh Token 都使用 `.env` 中的 `TABERU_MATE_AUTH_TOKEN_SECRET` 做 HMAC-SHA256 签名。
- Token 撤销：Access Token 使用 `jti` 撤销表；Refresh Token 使用服务端存储记录和 `revoked_at` 字段。
- Token 过期：`TABERU_MATE_ACCESS_TOKEN_EXPIRE_MINUTES` 控制 access token；`TABERU_MATE_REFRESH_TOKEN_EXPIRE_DAYS` 控制 refresh token。
- 会话固定攻击：每次登录和刷新都生成新的 `jti` 和签名，不复用旧 token。
- CSRF：非 GET 的认证状态变更接口使用双重提交 Cookie + Header，并且 Cookie 设置 `SameSite=Strict`。
- 暴力尝试：登录接口有简单的 IP + 用户名窗口限流，超过阈值返回 `429`。

## 错误处理与日志

- 本地环境保留 FastAPI 的详细校验错误，方便开发。
- `production`、`prod`、`staging` 环境会隐藏详细错误，将校验异常统一为 `400`，认证/权限异常统一为 `403`，限流异常为 `429`。
- 服务端会记录结构化安全事件日志，字段包含事件名、路径、方法、客户端 IP、User-Agent、用户名、用户 id、`jti` 和原因。
- 已记录的安全事件包括登录失败、登录限流、Access Token 缺失/无效/已撤销、Refresh Token 缺失/无效/拒绝、CSRF 失败和未处理异常。
- 当前实现输出 JSON 日志，可直接采集到 ELK；如果要接 Sentry，可通过 `TABERU_MATE_SENTRY_DSN` 作为配置入口扩展初始化逻辑。
