import os
import sys
import shutil
import ctypes
import pandas as pd

import DownloadPolicy as DP


def display_versions_and_choose(df):
    df = df.copy().sort_values('Channel', ascending=False)\
        .sort_values('Version', ascending=False).reset_index(drop=True)
    # 表の表示
    print(df[['Version', 'Channel']])
    print()

    # ユーザーに選択させる
    indexes = list(df.index)
    versions = list(df['Version'])
    print("To cancel, type 'c'.")
    chosen_input = ""
    while True:
        chosen_input = input("Enter index or version string (Default: Latest Stable):")
        chosen_input = chosen_input.strip()
        if chosen_input == 'c':
            return None
        if not chosen_input:  # デフォルトの選択（最新のStable版）
            latest_stable_version = df[df['Channel'] == 'stable']['Version'].max()
            return latest_stable_version
        if chosen_input.isdigit() and int(chosen_input) in indexes:
            return df.loc[int(chosen_input), 'Version']
        elif chosen_input in versions:
            return chosen_input

def is_admin():
    try:
        # 管理者権限で実行されているかを確認するために、os.getuid() を使用
        # Windowsでは、os.getuid()は存在しないので、AttributeErrorが発生
        return os.getuid() == 0
    except AttributeError:
        return os.system("net session >nul 2>&1") == 0


def copy_files_to_policy_dir(src_path=r"policy/windows/admx"):
    dest_path = "C:\\Windows\\PolicyDefinitions"
    # dest_path = "C:\\temp\\PolicyDefinitions"

    for item in os.listdir(src_path):
        src_item = os.path.join(src_path, item)
        dest_item = os.path.join(dest_path, item)

        # ファイルの場合
        if os.path.isfile(src_item):
            shutil.copy2(src_item, dest_item)
            print(f"{item} copied to {dest_path}.")
        # ディレクトリの場合
        elif os.path.isdir(src_item):
            if not os.path.exists(dest_item):  # ディレクトリが存在しない場合、新しく作成
                os.makedirs(dest_item)
            for sub_item in os.listdir(src_item):
                src_sub_item = os.path.join(src_item, sub_item)
                dest_sub_item = os.path.join(dest_item, sub_item)
                if os.path.isfile(src_sub_item):
                    shutil.copy2(src_sub_item, dest_sub_item)
            print(f"Contents of {item} directory copied to {dest_path}")


if __name__ == "__main__":
    try:
        # 管理者権限の確認
        if not is_admin():
            print("Administrative privileges are required to perform this operation.")

            # # UACプロンプトを表示して管理者権限でスクリプトを再実行
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
            exit(0)

        df = DP.get_versions()

        # ユーザーがバージョンを選択
        selected_version = display_versions_and_choose(df)
        print()
        print("Version:", selected_version)

        if not selected_version:
            print("Operation canceled.")
            input("Press Enter to exit.")
            exit(0)

        print("Downloading...\n")
        cab_filename = DP.download_version(selected_version, df)
        zip_filename = DP.extract_cab(cab_filename)
        if zip_filename:
            DP.extract_zip(zip_filename)

            # cab と zip ファイルを削除
            os.remove(cab_filename)
            os.remove(zip_filename)

            # ファイルを C:\windows\PolicyDefinitions にコピー
            copy_files_to_policy_dir()

        print()
        input("Press Enter to exit.")

    except Exception as e:
        print()
        print(e)
        input("Press Enter to exit.")