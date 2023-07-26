# -*- encoding:utf-8 -*-
"""
@用于下载视频
@2023年3月16日 05:20:33
"""
import os
import requests
import re
from concurrent.futures import ThreadPoolExecutor
import time


class Video2M3u8(object):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
    }
    argss = {
        'key': 'VmNTagBhVDEBNlc9UmBXPQs/VzMHcAdzAnZRMQIxCD8DPg80AGdTNgExUzpVYQ==',
             'name':'.m3u8'
    }
    def __init__(self, index_url):
        if index_url[-1] == "/" or index_url[-1] == "\\":
            self.url = index_url[:-1]
        else:
            self.url = index_url
        self.m3u8_dict = {}

    def m3u8_analysis(self):
        """
        分析重定向(嵌套流)
        :return:
        """
        while True:
            try:
                resp = requests.get(self.url, headers=self.headers, timeout=10).text
            except Exception:
                pass
            else:
                break
        if "#EXT-X-STREAM-INF:" in resp:
            # 存在嵌套关系 先假设只有一个嵌套链接
            resp_list = re.findall("(.*)\n", resp)
            resolution = re.findall("RESOLUTION=(.*)\n", resp)
            bandwidth = re.findall("BANDWIDTH=(.*),", resp)
            j = False
            for n in resp_list:
                if j:
                    j = False
                    new_url = "https://" + re.findall("://(.*?)/", self.url)[0] + n
                    self.url = new_url
                if "#EXT-X-STREAM-INF:" in n:
                    j = True
            self.m3u8_dict = {
                'resolution': resolution[0],
                "url": new_url,
                'bandwidth': bandwidth[0],
                "EXT-X-KEY": "未知"
            }
            return self
        else:
            resp_list = re.findall("(.*)\n", resp)
            j = False
            stream_video = []
            stream_time = []
            for n in resp_list:
                if "#EXT-X-KEY" in n:
                    self.m3u8_dict["EXT-X-KEY"] = re.findall("#EXT-X-KEY:(.*?),", resp)
                    self.m3u8_dict["URI"] = re.findall("URI=(.*?)\n,", resp)
                else:
                    self.m3u8_dict["EXT-X-KEY"] = "未加密"
                # 判断流
                if j:
                    j = False
                    if "/" not in n:
                        stream_video.append((self.url[:self.url.rindex("/") + 1] + "/" + n).rstrip())
                    elif "//" in n:
                        stream_video.append(n.rstrip())
                    else:
                        stream_video.append(("https://" + re.findall("://(.*?)/", self.url)[0] + n).rstrip())
                # 流时长
                if "#EXTINF:" in n:
                    j = True
                    stream_time.append(re.findall("#EXTINF:(.*?),", n)[0])

                # 结束
                if "#EXT-X-ENDLIST" in n:
                    pass
            self.m3u8_dict["stream_video_len"] = len(stream_video)
            self.m3u8_dict["stream_time_len"] = len(stream_time)
            self.m3u8_dict["stream_video"] = stream_video
            self.m3u8_dict["stream_time"] = stream_time
            return self

    def thread_down(self, path, url):
        j = True
        while j:
            try:
                r = requests.get(url.rstrip(), headers=self.headers, timeout=20).content
            except Exception as e:
                j = True
            else:
                with open(path, mode="wb") as f:
                    f.write(r)
                if os.path.getsize(path) < 1024:
                    j = True
                else:
                    j = False

    def m3u8_down(self, *args, **kwargs):
        stream_video = self.m3u8_dict["stream_video"]
        # 多线程===========
        p = "./temp"
        if os.path.exists(p):
            for n in os.listdir(p):
                os.remove(p + "/" + n)
            os.removedirs(p)
        if not os.path.exists(p):
            os.makedirs(p)
        if not os.path.exists(kwargs['save'][:kwargs['save'].rindex("/")]):
            os.makedirs(kwargs['save'][:kwargs['save'].rindex("/")])
        with ThreadPoolExecutor(20) as pool:
            for n in range(len(stream_video)):
                pool.submit(self.thread_down, f"{p}/{n}.ts", stream_video[n])
            pool.shutdown(wait=True)
        lst_dir = os.listdir(p)
        lst_dir.sort(key=lambda x: int(re.findall(r"(\d+).ts", x)[0]))
        with open("./file.txt", mode="w", encoding="utf-8") as fw:
            for k in lst_dir:
                fw.write(f"""file '{os.path.abspath(p + "/" + k)}'\n""")
        cmd = rf"C:\Users\Administrator\Desktop\pythonProcess\ffmpeg-5.1.2-essentials_build\bin\ffmpeg.exe -f concat -safe 0 -i {os.path.abspath('./file.txt')}  -acodec copy -vcodec copy -f mp4 {os.path.abspath(kwargs['save'])}"
        os.system(cmd)
        for n in os.listdir(p):
            os.remove(p + "/" + n)
        os.removedirs(p)
        os.remove('./file.txt')
        # =================
        return self


class HtmlM3u8(object):
    headers = {
        "User-Agent": "Mozilla/5.0(Windows NT 10.0;WOW64)AppleWebKit/537.36KHTMLlikeGecko)Chrome/86.0.4240.198Safari/537.36",
        'Connection': 'keep-alive',
    }

    def __init__(self, html_url, title="None"):
        self.url = html_url
        self.url_m3u8_dict = {}
        self.url_lst = []
        self.title = title

    def html_analysis(self):
        resp = requests.get(self.url, headers=self.headers).text
        url = re.findall(r'<script.*>.*player_aaaa=.*"url":"(.*?)",.*</script>', resp)[0].replace(r"\/", "/")
        url_next = re.findall(r'<script.*>.*player_aaaa=.*"url_next":"(.*?)",.*</script>', resp)[0].replace(r"\/", "/")
        link = re.findall(r'<script.*>.*player_aaaa=.*"link":"(.*?)",.*</script>', resp)[0].replace(r"\/", "/")
        link_next = re.findall(r'<script.*>.*player_aaaa=.*"link_next":"(.*?)",.*</script>', resp)[0].replace(r"\/",
                                                                                                              "/")
        host = re.findall(r"https://(.*?)/", self.url)[0]
        self.url_m3u8_dict = {
            'link': "https://" + host + link,
            'link_next': "https://" + host + link_next,
            "url": url,
            "url_next": url_next}
        return self

    def total_url(self):
        while True:
            self.url_lst.append(self.url_m3u8_dict["url"])
            if self.url_m3u8_dict["url_next"] == '':
                break
            self.url = self.url_m3u8_dict["link_next"]
            self.html_analysis()



def main():
    u = input("url:")
    title = input("title:")
    t = {
        "url": u,
        "title": title
    }
    hm = HtmlM3u8(t['url'], title=t['title'])
    hm.html_analysis()
    hm.total_url()
    print(hm.url_lst)
    count = 0
    for k in hm.url_lst:
        count += 1
        vm = Video2M3u8(k)
        v = vm.m3u8_analysis().m3u8_analysis()
        print(vm.m3u8_dict)
        vm.m3u8_down(save=f"./{hm.title}/{hm.title}_{count}.mp4")


if __name__ == '__main__':
    # main()
    vm = Video2M3u8("https://cdn18.yzzy-kb-cdn.com/20230724/1551_f0ff975d/2000k/hls/index.m3u8")
    v = vm.m3u8_analysis().m3u8_analysis()
    print(vm.m3u8_dict)
    vm.m3u8_down(save=f"./ZZ/4.mp4")