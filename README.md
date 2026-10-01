# Sonoff S31：GitHub OTA 與 Home Assistant 更新

此專案以提供的 S31 YAML 為基礎，加入 HTTP OTA、HA 更新實體、手動檢查更新按鈕及記憶體診斷。功率改為每 0.5 秒發布平均值，移除會干擾電量積分的 delta 濾波。

## 檔案

- `sonoff-s31.yaml`：完整 S31 設定，保留原本裝置名稱與 MAC 後綴。
- `ota.yaml`：共用 OTA 設定與目前韌體版本。
- `requirements.txt`：固定 ESPHome 2026.9.1，避免編譯工具自動升版。
- `.github/workflows/validate.yaml`：修改設定後自動驗證及編譯，不發布。
- `.github/workflows/publish.yaml`：手動指定版本，編譯並發布到 GitHub Pages。
- `scripts/make_manifest.py`：從實際 OTA binary 計算 MD5，產生 manifest。

## 第一次使用

1. 儲存原本在 ESPHome Device Builder 中的 YAML 備份。
2. 在 GitHub 的 **Settings → Pages → Build and deployment → Source** 選 **GitHub Actions**。發布 workflow 也會嘗試啟用 Pages；若權限不允許，請手動設定。
3. 在 **Actions → Publish S31 OTA → Run workflow**，選 `main`，版本填 `1.0.0`。
4. 等待 build 和 deploy 都成功。確認下列 URL 能直接顯示 JSON：
   `https://davidjetw.github.io/Sonoff-S31/firmware/manifest.json`
5. 把 `ota.yaml` 放進 HA 的 ESPHome 設定目錄，在原本 S31 YAML 最外層加入：

   ```yaml
   packages:
     github_ota: !include ota.yaml
   ```

   如果原本已有 packages，請合併。原本的 `ota: - platform: esphome` 必須保留；原本如果已有 debug 或 Heap Free／Heap Max Block，請移除重複的診斷實體。
6. 原本 `power:` 的 filters 改成 `- throttle_average: 0.5s`。使用 ESPHome 2026.9.1 或同版本 Device Builder，先 **Validate**，再透過現有 ESPHome OTA 安裝。這是首次啟用 HTTP OTA 的必要步驟；只把舊 bin 放到 GitHub 不會讓裝置得到新功能。
7. 在 HA 的 S31 裝置頁確認 `Firmware Update`、`Check Firmware Update`、`Firmware Version` 出現。已有 Wi-Fi 資料的裝置使用原本設定；如果更新後無法連線，使用 fallback AP/captive portal 重新配網。

亦可直接使用完整 `sonoff-s31.yaml`，但請先比較你的最新本機設定，確保名稱、API、OTA 密碼與個別設定一致。完整範例沒有 Wi-Fi SSID、Wi-Fi 密碼、API 加密金鑰或私人 OTA 密碼，使用 captive portal 配網。公開韌體不應含這些私人資訊。

## 之後發布更新

1. 在 GitHub 修改並提交 `sonoff-s31.yaml`／`ota.yaml` 的功能。
2. 等 **Validate and compile S31** 成功。
3. **Publish S31 OTA → Run workflow**，填新的版本，例如 `1.0.1`。workflow 將同一版本寫入韌體及 manifest。
4. 建議同時更新 `ota.yaml` 裡的 `firmware_version`，讓本機編譯時的版本與發布版本一致。不要用較舊程式碼重複發布相同版本。
5. HA 按 `Check Firmware Update`，再從 `Firmware Update` 安裝。裝置每 6 小時只檢查版本，不會自動安裝。

請依序先在一顆 S31 上測試，確認功率、用電量、繼電器及記憶體正常，再更新第二顆。OTA 完成會重啟，繼電器會依原本通電狀態設定操作，請安排可中斷負載的時間。

## 更新來源與檔案

manifest：`https://davidjetw.github.io/Sonoff-S31/firmware/manifest.json`

只發布新編譯的 `firmware.ota.bin`，不使用 factory 格式，也不把儲存庫既有的 `sonoff-s31 (2026.5.3).bin` 當成新版。每次 MD5 自動從發布的同一個檔案計算，避免錯配。最新部署僅包含最新版本；若舊版清單的檔案已不存在，請重新檢查更新。

## 記憶體與限制

- S31 使用 ESP8266，設定保持 `board: esp12e`。
- HTTPS 接收 buffer 設為 16KB。已知原配置 Heap Free 約 35KB／Max Block 約 30KB，加入後仍需觀察實機；編譯 RAM 數字不包含所有動態連線分配。
- 若 HTTPS 更新出現記憶體不足或重啟，可先移除 `web_server:`；HA API 與 OTA 不依賴 web server。
- ESP8266 的 HTTP Request 元件要求 `verify_ssl: false`；會加密傳輸但不驗證伺服器憑證。MD5 只檢查檔案完整性，並非數位簽章或身分驗證。
- 此次加入 OTA，沒有重寫原本過載保護／自動恢復／雙 light 共用 output 邏輯；先前指出的過載恢復與 LED 競爭問題仍應另外修正。請勿把這份設定視為已完成保護邏輯重構。
- 更新可用性仍需首次實機驗證，不能只由 YAML 驗證成功推定。

## 本機編譯

```sh
python -m pip install -r requirements.txt
esphome config sonoff-s31.yaml
esphome compile sonoff-s31.yaml
```

## 官方文件

- [HTTP OTA](https://esphome.io/components/ota/http_request/)
- [版本清單格式](https://esphome.io/components/update/http_request/)
- [ESP8266 HTTPS 限制](https://esphome.io/components/http_request/)
- [GitHub Pages Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
