import requests
import json
import winreg  # Windowsのレジストリを操作するためのモジュール

# 🔹 レジストリからAPIキーとリージョンを取得
def get_registry_value(key_path, value_name, hive=winreg.HKEY_LOCAL_MACHINE):
    try:
        with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
    except FileNotFoundError:
        print(f"⚠️ レジストリキーが見つかりません: {key_path}\\{value_name}")
        return None

# 🔹 レジストリの保存パス
REGISTRY_PATH = r"SOFTWARE\SpeechService"
# 🔹 APIキー & リージョンを取得
TRANSLATOR_KEY = get_registry_value(REGISTRY_PATH, "TRANSLATOR_KEY_VALUE", hive=winreg.HKEY_LOCAL_MACHINE)
SERVICE_REGION = get_registry_value(REGISTRY_PATH, "REGION_VALUE", hive=winreg.HKEY_LOCAL_MACHINE)
# 🔹 取得したキーを確認（デバッグ用）
if not TRANSLATOR_KEY:
    raise RuntimeError("❌ Translator APIキーの取得に失敗しました。レジストリを確認してください。")
if not SERVICE_REGION:
    raise RuntimeError("❌ リージョンの取得に失敗しました。レジストリを確認してください。")
print(f"✅ Translator APIキー取得成功: {TRANSLATOR_KEY[:5]}...（セキュリティのため一部のみ表示）")
print(f"✅ リージョン取得成功: {SERVICE_REGION}")
# 🔹 Azure Translator APIの設定
TRANSLATOR_ENDPOINT = "https://api.cognitive.microsofttranslator.com/translate"

def translate_text(text, from_lang="ja", to_lang="en"):
    """ Azure Translator API を使ってテキストを翻訳する """
    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": SERVICE_REGION,
        "Content-Type": "application/json"
    }
    params = {
        "api-version": "3.0",
        "from": from_lang,
        "to": to_lang
    }
    body = [{"text": text}]
    response = requests.post(TRANSLATOR_ENDPOINT, params=params, headers=headers, json=body)
    if response.status_code == 200:
        translated_text = response.json()[0]["translations"][0]["text"]
        print(f"✅ 翻訳成功: {translated_text}")
        return translated_text
    else:
        print(f"❌ 翻訳エラー: {response.status_code}, {response.text}")
        return None

def main():
    """ メイン処理 """
    text_to_translate = "今日は良い天気ですね。"  # 翻訳する日本語テキスト
    print(f"🌍 翻訳前: {text_to_translate}")

    translated_text = translate_text(text_to_translate)
    if translated_text:
        print(f"🌍 翻訳後: {translated_text}")

# 🔹 スクリプトのエントリーポイント
if __name__ == "__main__":
    main()
