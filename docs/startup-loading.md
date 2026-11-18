# 月面任务的启动资源加载

月面任务现在优先从作者的 Cloudflare HTTPS 资源域名读取启动 ZIP 的对应分段，显示实际下载进度，并把核对通过的原始 gzip 资源保存在浏览器 CacheStorage 中。之后再次打开时优先读取已验证缓存；CDN 读取失败或内容与记录不符时，回退到项目原来的五个静态文件。

启动资源共29,043,171字节，包括完整真实碰撞世界、显示网格、M20网格、任务配置与MuJoCo WASM。外层 ZIP 使用 stored 格式，可以按固定偏移直接读取内部 `.gz`，无需增加解压库。若服务器忽略 Range 并返回完整 ZIP，则共享同一次整包下载，再提取对应资源。

每份资源在进入原初始化流程前都核对大小和SHA-256；损坏缓存不会被采用。原gzip、XML/网格、控制、观测、模型预演、准入门槛和V3报告保持，加载完成后仍由同一MuJoCo物理模型实际初始化并接受操作。

## 资源来源

Cloudflare资源：

```text
https://nxzcdn.ycoroy.com/BeforeStep-startup-cdn-assets-20261118.zip
```

运行请求带`v=cdn-startup-20261118`以避开旧的缺少CORS许可的缓存响应。源配置、5个偏移与原SHA见[加载清单](../site/startup-assets.json)。

作者另提供Gitee发布附件作为下载备份；规范发布地址的跨域跳转当前未通过浏览器读取核查，因此没有将它启用为网页运行源，也没有硬编码临时签名地址。

## 验证

```bash
node tools/beforestep_mission/check_startup_loader.mjs
node tools/beforestep_mission/check_insight.mjs
node tools/beforestep_mission/check_playability.mjs
```

加载检查使用仓库原5资源构建有效ZIP，覆盖分段/完整ZIP、缓存零网络、损坏缓存丢弃与损坏CDN/CORS失败回退。真实浏览器另验证Cloudflare加载、持久缓存、M20显示、原模型转看、两世界完整预演、认证驾驶和键盘接管。

公网耗时与验证范围见[加载验证记录](../evidence/loading-20261118/verification.json)。网络条件、设备和物理初始化均影响等待时间；缓存命中表示不再下载启动资源，仍需准备真实物理模型。
