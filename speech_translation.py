import azure.cognitiveservices.speech as speechsdk
import requests
import winreg
import simpleaudio as sa
from convertwav import ConvertWAV

# 🔹 レジストリから API キーを取得
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
# 🔹 Azure APIキー & 設定の取得
SPEECH_SERVICE_APIKEY1 = get_registry_value(REGISTRY_PATH, "SPEECH_SERVICE_APIKEY1")
SPEECH_SERVICE_REGION = get_registry_value(REGISTRY_PATH, "SPEECH_SERVICE_REGION")
# 🔹 Azure Speech APIs
SPEECH_SERVICE_SPEECH_STT = get_registry_value(REGISTRY_PATH, "SPEECH_SERVICE_SPEECH_STT")
SPEECH_SERVICE_SPEECH_TTS = get_registry_value(REGISTRY_PATH, "SPEECH_SERVICE_SPEECH_TTS")
# 🔹 TRANSLATOR API のエンドポイント
SPEECH_SERVICE_TRANSLATOR_TXT = get_registry_value(REGISTRY_PATH, "SPEECH_SERVICE_TRANSLATOR_TXT")


# 🔹 言語設定の自動判別
def get_translation_languages(audio_file):
    """ ファイル名に `_jp` または `_en` が含まれているかで翻訳言語を決定 """
    if "_jp" in audio_file:
        return "ja", "en"  # 日本語 → 英語
    elif "_en" in audio_file:
        return "en", "ja"  # 英語 → 日本語
    else:
        return "ja", "en"  # デフォルト（日本語 → 英語）


# 🔹 音声を再生する関数
def play_audio(audio_file):
    try:
        print(f"▶️ 再生中: {audio_file}")
        wave_obj = sa.WaveObject.from_wave_file(audio_file)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"❌ 音声再生エラー: {e}")


# 🔹 STT: 音声 → テキスト
def recognize_speech_from_audio(audio_file):
    """
    音声ファイルをSTT（音声→テキスト）にかける
    :param audio_file: 音声ファイルのパス
    :return: 認識されたテキスト または None（失敗時）
    """
    print(f"🎤 音声認識開始: {audio_file}")
    # 音源の再生
    play_audio(audio_file)
    # 音声ファイルの確認と変換
    converter = ConvertWAV(audio_file)
    if not converter.check_audio_properties():
        print(f"⚠️ フォーマット不一致: 変換を実施")
        converted_file = "converted_" + audio_file
        audio_file = converter.convert_audio_format(converted_file) or audio_file

    try:
        print("🔧 SpeechConfig 設定中...")
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_SERVICE_APIKEY1, region=SPEECH_SERVICE_REGION)
        speech_config.set_property(
            property_id=speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
            value="10000"
        )

        # 言語設定（自動判別）
        source_lang, _ = get_translation_languages(audio_file)
        speech_config.speech_recognition_language = f"{source_lang}-JP" if source_lang == "ja" else "en-US"
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        print("🎤 音声認識中...")
        result = recognizer.recognize_once()
        print(f"🟡 STT 結果: {result.reason}")
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print(f"✅ 認識結果: {result.text}")
            return result.text
    except Exception as e:
        print(f"❌ STT処理中にエラーが発生: {e}")
    return None


# 🔹 翻訳API
def translate_text(text, audio_file):
    # ConvertWAV のインスタンスを作成
    converter = ConvertWAV(audio_file)
    # 翻訳前に日付フォーマットを変換
    text = converter.normalize_dates(text)  # インスタンスメソッドなので、converterを通じて呼び出す
    print(f"🌍 翻訳開始: {text}")

    # 翻訳元と翻訳先を決定
    source_lang, target_lang = get_translation_languages(audio_file)

    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_SERVICE_APIKEY1,
        "Ocp-Apim-Subscription-Region": SPEECH_SERVICE_REGION,
        "Content-Type": "application/json"
    }
    params = {"api-version": "3.0", "from": source_lang, "to": target_lang}
    body = [{"text": text}]

    try:
        response = requests.post(f"{SPEECH_SERVICE_TRANSLATOR_TXT}/translate", params=params, headers=headers, json=body)
        if response.status_code == 200:
            translated_text = response.json()[0]["translations"][0]["text"]
            print(f"✅ 翻訳結果: {translated_text}")
            return translated_text
    except Exception as e:
        print(f"❌ 翻訳処理中にエラーが発生: {e}")

    return None


# 🔹 TTS: テキスト → 音声
def text_to_speech(text, audio_file):
    print(f"🗣️ 音声合成開始: {text}")

    # 翻訳先の言語を取得
    _, target_lang = get_translation_languages(audio_file)
    output_file = f"output_{target_lang}.wav"

    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_SERVICE_APIKEY1, region=SPEECH_SERVICE_REGION)
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"✅ 音声合成成功: {output_file}")
            play_audio(output_file)  # 🎵 生成した音声を再生
    except Exception as e:
        print(f"❌ TTS処理中にエラーが発生: {e}")


# 🔹 メイン処理
def main():

    # wavファイル
    audio_file = "sample_en.wav"
    print(f"📢 使用する音声ファイル: {audio_file}")

    # 🔹 STT: 音声 → テキスト
    recognized_text = recognize_speech_from_audio(audio_file)
    if not recognized_text:
        return

    # 🔹 翻訳API
    translated_text = translate_text(recognized_text, audio_file)
    if not translated_text:
        return

    # 🔹 TTS: テキスト → 音声
    text_to_speech(translated_text, audio_file)


# 🔹 スクリプトのエントリーポイント
if __name__ == "__main__":
    main()
