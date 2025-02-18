import azure.cognitiveservices.speech as speechsdk
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
SPEECH_KEY = get_registry_value(REGISTRY_PATH, "TRANSLATOR_KEY_VALUE", hive=winreg.HKEY_LOCAL_MACHINE)
SERVICE_REGION = get_registry_value(REGISTRY_PATH, "REGION_VALUE", hive=winreg.HKEY_LOCAL_MACHINE)

# 🔹 取得したキーを確認（デバッグ用）
if not SPEECH_KEY:
    raise RuntimeError("❌ Speech Synthesis APIキーの取得に失敗しました。レジストリを確認してください。")
if not SERVICE_REGION:
    raise RuntimeError("❌ リージョンの取得に失敗しました。レジストリを確認してください。")

print(f"✅ Speech Synthesis APIキー取得成功: {SPEECH_KEY[:5]}...（セキュリティのため一部のみ表示）")
print(f"✅ リージョン取得成功: {SERVICE_REGION}")

def text_to_speech(text, output_file="output.wav", voice="en-US-JennyNeural"):
    """ Azure Speech Synthesis API を使ってテキストを音声に変換する """
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)

    # 🔹 音声設定（音声モデル: en-US-JennyNeural）
    speech_config.speech_synthesis_voice_name = voice

    # 🔹 音声合成を実行
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()

    # 🔹 結果の確認
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"✅ 音声合成成功: {output_file} に保存しました。")
        return output_file
    elif result.reason == speechsdk.ResultReason.Canceled:
        print(f"❌ 音声合成エラー: {result.cancellation_details.reason}")
        return None

def main():
    """ メイン処理 """
    text_to_speak = "It's nice weather today, isn't it?"  # 例: 翻訳した英語テキスト
    print(f"🗣️ 音声合成対象のテキスト: {text_to_speak}")

    output_file = text_to_speech(text_to_speak)
    if output_file:
        print(f"🔊 生成された音声ファイル: {output_file}")

# 🔹 スクリプトのエントリーポイント
if __name__ == "__main__":
    main()
