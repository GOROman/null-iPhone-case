# NULL PAPER

M5Stack PaperDIY（K159 / K159-B）とケース v0.40 用のファームウェアです。iPhone で選んだ写真や URL の QR コードを背面の大きな丸窓に表示します。USB が下、カメラが上の向きで使います。

## セットアップ

1. PlatformIO Core を用意し、リポジトリのルートで次のコマンドを実行します。

   ```sh
   pio run -d firmware
   ```

2. PaperDIY をデータ通信対応の USB-C ケーブルで接続します。電源ボタンを長押しし、赤い LED が点滅したら離して、次のコマンドで書き込みます。ポートを指定する場合は末尾に `--upload-port /dev/cu.…` を追加します。書き込みで本体の既存ファームウェアとパーティション構成が置き換わります。[M5Stack の製品・書き込み手順](https://docs.m5stack.com/en/core/PaperDIY_Assembly_Kit)

   ```sh
   pio run -d firmware -t upload
   ```

3. Xcode で [NullPaper.xcodeproj](../ios/NullPaper.xcodeproj) を開き、NullPaper ターゲットの Signing & Capabilities で自分の Team を選びます。iOS 17 以降の iPhone を実行先に選び、Run します。

## 写真を表示する

1. アプリで「写真を選ぶ」を押します。中央を正方形に切り抜いた写真が、実際に送る16階調の丸窓プレビューに表示されます。
2. PaperDIY の電源ボタンを1回押し、アプリで「ケースを探す」から「NULL PAPER」を選びます。初回は iOS のペアリング要求を許可します。
3. 「写真をケースに送る」を押します。「ケースの表示を更新しました」と出たら完了です。時計の動作中に次の写真を送るときは、A ボタンで接続待ちを開始します。

## URL を QR コードで表示する

1. アプリで「URL・QR」を選び、HTTP または HTTPS の URL を貼り付けて「QRコードを作成」を押します。
2. 丸窓プレビューを確認したらケースの電源を入れ、接続して「QRコードをケースに送る」を押します。最後に送った画像1枚が保存されます。
3. 別のスマートフォンのカメラをケースの丸窓に向けると、リンクを読み取れます。電子ペーパーの表示は電源オフ後も使えます。

QR コードは iPhone 内で生成します。白い余白を4セル分確保し、黒いセルは整数ピクセルで描画します。1セルが4ピクセル未満になる長い URL では、アプリに短い URL を入力するよう案内が出ます。

## ケースの窓と時計

| 窓 | 表示 |
| --- | --- |
| 大きな丸窓 | 初期画面は MUSE の Jollybot と「NULL PAPER」。写真または QR コードを送ると切り替わります。 |
| 右の3窓 | 上から電池残量の推定値、Wi-Fi 有効の仮表示、Bluetooth のアイコン。 |
| 横長の窓 | CODEX WEEKLY 68%、CLAUDE WEEKLY 72%、MUSE。週次の2値には手入力した値を表示します。右端のアンテナは仮表示で3本点灯します。 |
| 一番下の丸窓 | 時針・分針・秒針のアナログ時計。未同期のときは針を12時位置に待機させ、「SYNC」を表示します。 |

時計は iPhone アプリの接続時に現地時刻に合います。電池切れや完全な電源オフの後、またはタイムゾーンや夏時間が変わったときは再接続してください。Mac から時刻を合わせる場合は PaperDIY を起動し、pyserial が入った Python で次のコマンドを実行します。

```sh
python3 firmware/tools/sync_clock.py /dev/cu.usbmodem2101
```

表示位置は v0.40 の CAD 座標から USB 側へ39ピクセル（約4.2 mm）補正しています。実際のケースとの中心合わせは [dashboard.h の offsetY](src/dashboard.h) で調整できます。

文字と時計の数字には [NULL FONT](../null-font) のアウトラインを4倍で描いて縮小し、一覧は24 px、時計・残量は30 px、タイトルは36 pxの等倍で表示します。Jollybot の絵は初回ビルド時に Muse Gadget SDK の固定リビジョンから取得し、happy アニメーションの先頭フレームを16階調に変換します。キャラクター素材には SDK 本体と別の利用条件が適用されます。[MUSE 公式素材](https://github.com/facebookincubator/muse-gadget-sdk/tree/18dcce3d9b6eb845c7ab859a33488be66a58fba2/esp32/avatar) · [上流のライセンス表記](https://github.com/facebookincubator/muse-gadget-sdk#license)

別の iPhone に登録し直す場合は、PaperDIY の A・B 両方を押しながら電源を入れ、起動後も約1秒押し続けます。これで本体のペアリング情報を消去します。以前の iPhone で再登録するときは、iOS の Bluetooth 設定から古い登録も解除してください。

## バッテリー動作

- 手動で起動すると BLE 接続を受け付けます。待ち受けは無操作で60秒、転送途中は最後のパケットから20秒で終了します。Wi-Fi は使用しません。
- 転送は暗号化・ボンディングした接続で行います。全51,200バイトの長さ、順序、CRC32 を確認してから保存し、電子ペーパーを1回更新します。同じ画像を再送した場合は再描画とフラッシュ書き込みを省きます。
- 画面更新後はパネルをスリープさせます。接続が終了すると、時刻同期済みなら BLE を終了し、各秒の間は ESP32-S3 をライトスリープにします。秒針は時計の280×280ピクセルだけを高速更新し、分が変わると同じ領域の残像を消去します。時刻が未設定なら M5PM1 で本体を電源オフにします。使用可能日数は実測前です。[M5Stack 公式ファームウェア](https://github.com/m5stack/M5PaperDIY-UserDemo)

## 動作確認

iOS の写真変換・QR 読み取りテストは Xcode の Test で実行できます。受信処理のテストはリポジトリのルートで以下を実行します。

```sh
c++ -std=c++17 firmware/test/receiver.cpp -o /tmp/null-paper-receiver && /tmp/null-paper-receiver
```
