import yaml
import requests
import sys
import os
import socket

from yaml.loader import FullLoader

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print("Usage:")
    print("    python3 helper.py <input> [output]")
    print("Example:")
    print("    python3 helper.py myTmp1.yaml")
    print("    python3 helper.py myTmp2.yaml output2.yaml")
    exit(1)


class Site:

    def __init__(self, name: str, group: str, url: str, inclusion: list, exclusion: list, dedup: bool):
        self.name = name
        self.group = group
        self.url = url
        self.inclusion = inclusion
        self.exclusion = exclusion
        self.nodes = []
        self.dedup = dedup

        status_code = 200
        try:
            headers = {
                "User-Agent": "ClashForAndroid/2.5.12",  # V2board 根据 UA 下发配置
            }
            r = requests.get(url, headers=headers)
            status_code = r.status_code
            assert status_code == 200
            self.data = yaml.load(r.text, Loader=FullLoader)
            # 缓存
            with open("{}.yaml".format(name), "w", encoding="utf-8") as f:
                f.write(r.text)
        except Exception as e:
            if status_code != 200:
                self.log(f"HTTP Error: {status_code}")
            self.log("加载异常")
            if os.path.exists("{}.yaml".format(name)):
                self.log("使用上次缓存")
                with open("{}.yaml".format(name), "r", encoding="utf-8") as f:
                    self.data = yaml.load(f, Loader=FullLoader)
            else:
                self.data = None
                self.log("节点组为空")

    def purge(self):
        self.nodes = self.data['proxies']
        nodes_good = []

        # blacklist keywords
        if self.exclusion:
            for node in self.nodes:
                flag = True
                for k in self.exclusion:
                    if k in node['name'].lower() or k in node['server'].lower():
                        self.log("Drop: {}".format(node['name']))
                        flag = False
                        break
                if flag:
                    nodes_good.append(node)

            self.nodes = nodes_good
            nodes_good = []

        # whitelist keywords
        if self.inclusion:
            for node in self.nodes:
                for k in self.inclusion:
                    if k in node['name'].lower() or k in node['server'].lower():
                        nodes_good.append(node)
                        break

            self.nodes = nodes_good
            nodes_good = []

        # deduplicate
        if self.dedup:
            used = set()
            for node in self.nodes:
                try:
                    ip = socket.getaddrinfo(node['server'], None)[0][4][0]
                    p = (ip, node['port'])
                    if p in used:
                        self.log("Drop: {}, dup!".format(node['name']))
                    else:
                        self.log("Take: {}".format(node['name']))
                        nodes_good.append(node)
                        used.add(p)
                except:
                    self.log(f"Failed to resolve node {node['name']}: {node['server']}")
            self.nodes = nodes_good
        else:
            self.log("Dedup disabled")
            for node in self.nodes:
                self.log("Take: {}".format(node['name']))

    def get_titles(self):
        return list(map(lambda x: x['name'], self.nodes))

    def log(self, message: str):
        print("[{}] {}".format(self.name, message))


def from_config(config: dict) -> Site:
    # enable dedup by default
    if "dedup" not in config:
        config['dedup'] = True
    return Site(config['name'], config['group'], config['url'], config['inclusion'], config['exclusion'], config['dedup'])


with open("sites.yaml", "r", encoding="utf-8") as f:
    config = yaml.load(f, Loader=FullLoader)
    sites = []
    for c in config:
        c['inclusion'] = list(map(lambda x: x.lower(), c['inclusion']))
        c['exclusion'] = list(map(lambda x: x.lower(), c['exclusion']))
        site = from_config(c)
        sites.append(site)


with open(sys.argv[1], "r", encoding="utf-8") as f:
    config = yaml.load(f, Loader=FullLoader)

for site in sites:
    if site.data != None:
        try:
            site.purge()
            config['proxies'] += site.nodes
            config['proxy-groups'][list(map(lambda x: x['name'], config['proxy-groups'])).index(site.group)]['proxies'] += site.get_titles()
        except Exception as e:
            self.log(f"Failed to process {site.name}")
            self.log(e)

# 对节点名去重
config['proxies'] = list({x['name']: x for x in config['proxies']}.values())

output_file = sys.argv[2] if len(sys.argv) == 3 else "out.yaml"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(yaml.dump(config, default_flow_style=False, allow_unicode=True))
