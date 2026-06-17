# 等保测评命令 - 微信文章批量转 Markdown

> 等保测评命令总结合集（63篇）- 网络设备 / 数据库 / 服务器操作系统 / 中间件

## 目录结构

```
dengbao-batch/
├── urls.txt          # 微信文章链接清单（格式: 分类|标题|URL）
├── convert.py        # 转换脚本
├── requirements.txt  # Python 依赖
├── output/           # 转换后的 Markdown 文件
└── README.md
```

## 快速开始

### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

### 2. 准备链接

编辑 `urls.txt`，每行格式：
```
分类|标题|URL
```

### 3. 运行转换

```powershell
python convert.py
```

### 4. 查看结果

转换完成后，Markdown 文件输出到 `output/` 目录，按分类组织：

```
output/
├── 网络设备/
│   ├── 华为网络设备.md
│   ├── 华三（H3C）网络设备.md
│   └── ...
├── 数据库/
│   ├── PostgreSQL数据库.md
│   └── ...
├── 服务器操作系统/
│   ├── UbuntuServer.md
│   └── ...
└── 中间件/
    ├── tomcat.md
    └── ...
```

转换日志保存为 `conversion_log.json`，失败链接可单独重试。

## 依赖

- Python 3.8+
- requests
- tqdm

## 注意

- 需要网络连接访问微信文章（部分 IP 段可能被微信拦截）
- 转换 API 使用 `https://mp2md.leti.ltd`
- 每篇间隔 1 秒，避免请求过快
