import os
import zipfile
import subprocess
import platform
import pandas as pd
import requests
from bs4 import BeautifulSoup
import js2py


def get_versions():
    url = "https://www.microsoft.com/ja-jp/edge/business/download"
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.36"
    response = requests.get(url, allow_redirects=True, headers={"User-Agent": ua})
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')

    # window.__NUXT__ のデータを取得
    nuxt_data_script = soup.find("script", text=lambda t: t and "window.__NUXT__" in t).text
    policy_data = js2py.eval_js(nuxt_data_script).to_dict()

    major_releases_data = policy_data['fetch']['block-enterprise-downloads:0']['majorReleases']

    # データをDataFrameに変換
    df_list = []
    for major_release in major_releases_data:
        channel = major_release.get('channelId')
        releases = major_release.get('releases', [])
        for release in releases:
            version = release.get('fullVersion')
            policy_url = release.get('policyUrl')
            df_list.append({'Version': version, 'Channel': channel, 'PolicyURL': policy_url})

    df = pd.DataFrame(df_list)

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

    print(f"{filename} をダウンロードしました。")
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
    cab_filename = download_version('115.0.1901.200', df)
    zip_filename = extract_cab(cab_filename)
    if zip_filename:
        extract_zip(zip_filename)
        # cab と zip ファイルを削除
        os.remove(cab_filename)
        os.remove(zip_filename)
    print(get_latest_version(df))
