# ClashHelper

自动拉取、过滤、合并订阅节点至自己的 Clash 配置模板。

+ 筛选节点名称和地址：
  * `exclusion`: 丢弃无效节点，例如名称或地址包含 `127.0.0.1`、`官网` 
  * `inclusion`: 筛选仅含有特定关键词的节点，例如名称或地址包含 `香港`、`IPLC` 的节点
+ 拉取订阅失败时自动使用上次缓存
* 基于 `(ip, port)` 节点去重：丢弃使用相同入口 IP 和端口的重复节点

输出的配置文件不包含模板中的注释，不影响使用。

## 使用场景

搭配 [Github Actions](https://github.com/marketplace/actions/deploy-to-gist) 的 [cron jobs](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows) 使用，推送配置文件至 [Github Gist](https://gist.github.com/)。将 Gist 的 `raw` 链接配置为 Clash 客户端订阅链接即可。

## User Guide

使用前需要将网站订阅信息写在 `sites.yaml` 内。

```yaml
[
  {
    name: "mySite", # 网站名称，仅用于日志输出
    group: "myNodes", # 目标 proxy-groups 的代理组名
    url: "https://example.com/v1/abcd", # Clash 配置文件的订阅 URL
    exclusion: ["127.0.0.1", "1.1.1.1", "官网", "IPv6", "测试"], # 节点名称或地址包含这些关键词的节点会被丢弃
    inclusion: ["香港", "新加坡", "日本"], # 仅采纳包含这些关键词的节点
    dedup: False # 是否基于节点入口 IP 地址进行去重
  },
]
```

模板文件 (`template.yaml`) 是一个预置的 Clash 配置文件。使用前必须为站点创建对应的代理分组，如下方所示。程序运行后会将网站的节点 **追加** 至目标代理组的 `proxies` 列表。如果不需预置节点，列表也可以留空。

```yaml
proxy-groups:
  - name: "myNodes" # 目标代理组名，对应网站配置的 group 字段
    type: url-test
    proxies: [] # 筛选后的节点将被追加至此处
    url: "http://www.gstatic.com/generate_204"
    interval: 30
```

运行脚本，程序会抓取订阅节点，依次使用 exclusion 和 inclusion 列表来过滤优质节点，并删除解析 IP 地址重复的节点，最后将节点追加至指定的代理分组内，并生成配置文件。

```text
$ python3 helper.py
Usage:
    python3 helper.py <input> [output]
Example:
    python3 helper.py myTmp1.yaml
    python3 helper.py myTmp2.yaml output2.yaml
```