import os
import zipfile
import subprocess
import platform
import pandas as pd
import requests
from bs4 import BeautifulSoup
import js2py


def get_versions():
    url = "https://www.microsoft.com/ja-jp/edge/business/download?form=MA13FJ"
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
    response = requests.get(url, allow_redirects=True,
                            headers={
                                "User-Agent": ua,
                                'Accept-Language': 'ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                            },
                            timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')

    nuxt_data_script = soup.find("script", id="__NUXT_DATA__").text
    policy_data = js2py.eval_js(nuxt_data_script).to_dict()

    df_list = []
    for k in policy_data.keys():
        if type(policy_data[k]) == dict:
            if 'fullVersion' in policy_data[k].keys():
                full_version = policy_data[str(policy_data[k]['fullVersion'])]
                policy_url = policy_data[str(policy_data[k]['policyUrl'])]
                df_list.append({'Version': full_version, 'PolicyURL': policy_url})

    df = pd.DataFrame(df_list).sort_values('Version', ascending=False).reset_index(drop=True)
    
    df['MajorVersion'] = df['Version'].str.split('.').str[0].astype(int)
    canary_major_version = df['MajorVersion'].max()

    def _classify_channel(major_version):
        if major_version == canary_major_version:
            return 'canary'
        elif major_version == canary_major_version - 1:
            return 'beta'
        else:
            return 'stable'

    df['Channel'] = df['MajorVersion'].apply(_classify_channel)
    del df['MajorVersion']

    return df

def get_latest_version(df):
    channels = df['Channel'].unique()
    latest_versions = {}
    for c in channels:
        latest_versions[c] = df[df['Channel'] == c]['Version'].max()
    return latest_versions

def download_version(selected_version, df):
    # DataFrameから選択したバージョンのポリシーテンプレートのURLを取得
    policy_url = df[df['Version'] == selected_version]['PolicyURL'].iloc[0]

    # ファイル名を取得（URLの最後の部分）
    filename = policy_url.split('/')[-1]

    # ファイルをダウンロード
    response = requests.get(policy_url)
    with open(filename, 'wb') as file:
        file.write(response.content)

    print(f"{filename} downloaded.")
    return filename



def extract_cab(filename):
    # 実行環境がWindowsの場合はexpandコマンドを、それ以外の場合はcabextractコマンドを使用
    if platform.system() == "Windows":
        subprocess.run(["expand", filename, "-F:*", "./"+filename[:-3]+"zip"])
    else:
        subprocess.run(["cabextract", filename])

    # 解凍したファイルの中からzipファイルを探す
    for file in os.listdir('.'):
        if file.endswith(".zip"):
            return file

    return None

def extract_zip(zip_filename, path="policy"):
    # policy フォルダの作成（存在しない場合）
    if not os.path.exists(path):
        os.makedirs(path)

    # zipファイルをpolicyフォルダに解凍
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(path)

if __name__ == "__main__":
    # 使用例
    df = get_versions()
    cab_filename = download_version('129.0.2792.79', df)
    zip_filename = extract_cab(cab_filename)
    if zip_filename:
        extract_zip(zip_filename)
        # cab と zip ファイルを削除
        os.remove(cab_filename)
        os.remove(zip_filename)
    print(get_latest_version(df))
