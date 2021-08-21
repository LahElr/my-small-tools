import os
import pickle
from datetime import datetime
from joblib import Parallel, delayed

import requests
from tqdm import tqdm
import urllib3

headers = {
    # 'User-Agent': 'Googlebot-Image/1.0',
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.73',
    'X-Forwarded-For': '64.18.15.200',
    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language":
    "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "close",
    "DNT": "1",
    "session-id": "462-7637617-0706360",
}

proxies = {
    'http': 'http://127.0.0.1:10809',
    'https': 'http://127.0.0.1:10809',
    # 'socks5' : 'socks5://127.0.0.1:10808'
}

requests.packages.urllib3.disable_warnings()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def download_image(index, url, path):
    image_dir = os.path.join(path, str(index) + '.jpg')

    if os.path.isfile(image_dir):
        return
    
    if os.path.exists(image_dir):
        return

    try:
        response = requests.get(url,
                                stream=False,
                                timeout=5,
                                allow_redirects=True,
                                headers=headers,
                                proxies=proxies,
                                # verify=False
                                )
        with open(image_dir, 'wb') as file:
            response.raw.decode_content = True
            file.write(response.content)
    except:
        # print('failed to download {}'.format(url), flush=True)
        with open("failed_urls.log","a") as file:
            file.write("{} : {},\n".format(index,url))


with open('SBU_captioned_photo_dataset_urls.txt') as f:
    urls = f.readlines()

start = datetime.now()
# download images
try:
    Parallel(n_jobs=16)(delayed(download_image)(index, url, "img")
                       for index, url in enumerate(tqdm(urls[:-1])))
except KeyboardInterrupt:
    print("\nKeyboardInterrupt triggered.")

print("fin.")
