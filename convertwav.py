import wave
import numpy as np
import matplotlib.pyplot as plt
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import re

class ConvertWAV:
    def __init__(self, file_path):
        """
        初期化: WAVファイルのパスを指定
        :param file_path: 音声ファイルのパス
        """
        self.file_path = file_path

    def check_audio_properties(self):
        """
        WAVファイルのオーディオプロパティを表示
        - 正しいフォーマット (16kHz, 16bit, モノラル) かどうかを `bool` で返す
        """
        try:
            with wave.open(self.file_path, "rb") as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                bit_depth = wf.getsampwidth() * 8

                print(f"🔍 {self.file_path} のオーディオ情報")
                print(f"・チャンネル数: {channels}")
                print(f"・サンプルレート: {sample_rate} Hz")
                print(f"・ビット深度: {bit_depth} bit")
                print(f"・フレーム数: {wf.getnframes()}")
                print(f"・再生時間: {wf.getnframes() / wf.getframerate()} 秒\n")

                return channels == 1 and sample_rate == 16000 and bit_depth == 16
        except wave.Error as e:
            print(f"❌ WAVファイルの読み込みエラー: {e}")
            return False

    def convert_audio_format(self, output_file):
        """
        WAVファイルを 16kHz, 16bit, モノラル に変換
        """
        print(f"🎵 {self.file_path} を適切なフォーマットに変換中...")
        try:
            audio = AudioSegment.from_wav(self.file_path)
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(output_file, format="wav")
            print(f"✅ 変換完了: {output_file}")
            return output_file
        except Exception as e:
            print(f"❌ 音声変換エラー: {e}")
            return None

    def plot_waveform(self):
        """
        WAVファイルの波形をプロットする
        """
        with wave.open(self.file_path, "rb") as wf:
            frames = wf.readframes(-1)
            signal = np.frombuffer(frames, dtype=np.int16)

            plt.figure(figsize=(12, 4))
            plt.plot(signal, color="blue")
            plt.title(f"Waveform of {self.file_path}")
            plt.xlabel("Samples")
            plt.ylabel("Amplitude")
            plt.show()

    def remove_silence(self, output_file, silence_thresh=-40, min_silence_len=500):
        """
        WAVファイルの無音部分を検出し、除去する
        """
        print("🔍 無音部分を検出中...")
        try:
            audio = AudioSegment.from_wav(self.file_path)
            non_silent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

            if not non_silent_ranges:
                print("⚠️ 音声がすべて無音と判定されました")
                return

            start_trim = non_silent_ranges[0][0]
            end_trim = non_silent_ranges[-1][1]
            trimmed_audio = audio[start_trim:end_trim]
            trimmed_audio.export(output_file, format="wav")
            print(f"✅ 無音部分を除去して保存: {output_file}")
        except Exception as e:
            print(f"❌ 無音処理エラー: {e}")

    def normalize_dates(self, text):
        """
        テキスト内の日付表記を正しく変換する
        例: "February 17th 2025" → "2025年2月17日"
        """
        month_mapping = {
            "January": "1月", "February": "2月", "March": "3月",
            "April": "4月", "May": "5月", "June": "6月",
            "July": "7月", "August": "8月", "September": "9月",
            "October": "10月", "November": "11月", "December": "12月"
        }

        # "February 17th 2025" のような英語日付を抽出する正規表現 (
        date_pattern = re.compile(r"(\w+) (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})")

        def replace_date(match):
            month, day, year = match.groups()
            month_ja = month_mapping.get(month, month)
            return f"{year}年{month_ja}{int(day)}日"

        return date_pattern.sub(replace_date, text)
