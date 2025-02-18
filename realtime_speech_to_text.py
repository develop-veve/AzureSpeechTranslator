# Filename: realtime_speech_to_text.py
import azure.cognitiveservices.speech as speechsdk
import time
import winreg
import sys


def get_registry_value(key_path, value_name, hive=winreg.HKEY_LOCAL_MACHINE):
    try:
        with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
    except FileNotFoundError:
        print(f"⚠️ レジストリキーが見つかりません: {key_path}\\{value_name}")
        return None


REGISTRY_PATH = r"SOFTWARE\SpeechService"
SPEECH_SERVICE_APIKEY1 = get_registry_value(REGISTRY_PATH, "SPEECH_SERVICE_APIKEY1")
SPEECH_SERVICE_REGION = get_registry_value(REGISTRY_PATH, "SPEECH_SERVICE_REGION")


def recognize_from_microphone():
    if not SPEECH_SERVICE_APIKEY1 or not SPEECH_SERVICE_REGION:
        print("APIキーまたはリージョンが取得できません。")
        return

    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_SERVICE_APIKEY1, region=SPEECH_SERVICE_REGION)
    speech_config.speech_recognition_language = "ja-JP"  # 日本語音声認識を設定

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    print("リアルタイム音声認識を開始します。マイクに向かって話してください。")

    def recognized_cb(evt):
        text = evt.result.text
        print("認識結果: {}".format(text))
        if "プログラム終了" in text:
            print("プログラム終了コマンドを検出しました。セッションを終了します。")
            speech_recognizer.stop_continuous_recognition()

    def stop_cb(evt):
        print("認識終了: {}".format(evt))
        print("プログラムを終了してください。")
        nonlocal done
        done = True
        sys.exit()  # プログラムを終了

    done = False
    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    speech_recognizer.start_continuous_recognition()

    while not done:
        time.sleep(0.5)

    speech_recognizer.stop_continuous_recognition()


if __name__ == "__main__":
    recognize_from_microphone()
