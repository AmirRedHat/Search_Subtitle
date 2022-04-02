import requests
from multiprocessing import Pool
from bs4 import BeautifulSoup
import os
import sys
import urllib3
import pysubs2
from pysubs2.time import make_time

from time import time


class SearchSub:
    category: str = "movies"
    local_path: str = "./Downloaded_Subtitles"

    def __init__(self, target_name: str = None):
        print("[+] Searching for links")
        self.check_directory(path=self.local_path)
        urllib3.disable_warnings()
        if target_name:
            target_name = target_name.lower()
            target_name = target_name.replace(" ", "-")
        self.local_path = "%s/%s" % (self.local_path, target_name)
        self.check_directory(path=self.local_path)
        self.url = "https://worldsubtitle.site/%s/%s/" % (self.category, target_name)

    @staticmethod
    def check_directory(path):
        if not os.path.isdir(path):
            os.mkdir(path)

    @staticmethod
    def send_req(url):
        try:
            response = requests.get(url, headers={"Content-Type": "application/html"})
            if response.status_code == 200:
                return response.content
            else:
                print("[!] Not found any response for ", url)
                return None
        except Exception as error:
            print("Error Message : ", error)
            return None

    def process_response(self):

        response = self.send_req(url=self.url)
        if not response:
            return

        soup = BeautifulSoup(response, "html.parser")
        try:
            download_box = soup.find("div", attrs={"class": "single-box-body singleboxdl"})  # noqa
            get_ul_tag = download_box.find("ul")
            get_a_tag = get_ul_tag.find_all("a")
        except AttributeError:
            return

        link_list = [link["href"] for link in get_a_tag]
        self.download(link_list=link_list)

    def send_download_req(self, link):
        response = requests.get(link, stream=True, verify=False)
        if response.status_code == 200:
            content = response.content
        else:
            raise ConnectionError("[!] Connection failed")
        file_name = link.split("/")[-1]
        self.save(file_name=file_name, content=content)
        print("%s Downloaded" % file_name)

    def download(self, link_list: list):
        [self.send_download_req(link) for link in link_list]

    def save(self, file_name, content):
        file_name = "%s/%s" % (self.local_path, file_name)
        with open(file_name, "wb") as _file:
            _file.write(content)
            _file.close()

    @staticmethod
    def directory_files(_format: str = ".mkv") -> list:
        root_directory = "./"
        file_list = os.listdir(root_directory)
        return [f for f in file_list if f.endswith(_format)]

    @staticmethod
    def extract_filename(file_list: list):
        file_name_list = [file.split(".")[0] for file in file_list]
        print(file_name_list)


class EditSub:

    # TODO : should check the process
    def __init__(self, srt_file_path: str):
        if not self.check_path_file(srt_file_path):
            raise FileNotFoundError("srt file not found")
        self.file_path = srt_file_path

    @staticmethod
    def check_path_file(path):
        if os.path.isfile(path):
            return True
        return False

    def load_subtitle(self):
        return pysubs2.load(self.file_path)

    def process_subtitle(self, start_time: str, plus_time: int):
        loaded_sub = self.load_subtitle()
        h, m, s = start_time.split(":")
        made_time = make_time(h=int(h), m=int(m), s=int(s))
        print("made_time : ", made_time)

        line_list = [line.start for line in loaded_sub]
        line_index: int = 0
        lowest_different = None

        for line in line_list:
            # calculating lowest different between line and made_time
            if lowest_different is None:
                lowest_different = line
                continue
            
            if line > made_time:
                diff = line - made_time
                if diff < lowest_different:
                    lowest_different = line
            elif line < made_time:
                diff = made_time - line
                if diff < lowest_different:
                    lowest_different = line

        if line_index == 0 and lowest_different is not None:
            for line in line_list:
                if line == lowest_different:
                    line_index = line_list.index(line)
                    print(loaded_sub[line_index].start)
                    break

        # print("line Index: ", line_index)
        # for line in loaded_sub[line_index:]:
        #     print(line.text)
        #     line.start += plus_time
        #     line.end += plus_time


# app = EditSub(srt_file_path="./Nobody.2020.srt")
# app.process_subtitle(start_time="00:01:54", plus_time=5)

# python SearchSub.py search "..."
def worker(title: str):
    app = SearchSub(title)
    app.process_response()


def multiprocessing(title_list: list):
    with Pool(processes=len(title_list)) as pool:
        pool.map(worker, title_list)


if __name__ == "__main__":
    args = sys.argv
    command = args[1]

    if command == "search":
        titles_list = args[2]
        titles = [i.strip() for i in titles_list.split(",") if i]
        multiprocessing(titles)
    elif command == "directory_search":
        print("Not Implemented")
    else:
        print("command not found")
