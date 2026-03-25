# FamilyMart Laundry (全家自助洗衣) Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/PinLin/familaundry-homeassistant.svg?style=flat-square)](https://github.com/PinLin/familaundry-homeassistant/releases)
[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://github.com/hacs/integration)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

將全家自助洗衣 (Fami 自助洗衣) 的機台狀態整合到 Home Assistant，提供即時的洗烘進度監控。

## 功能特色
- **裝置化管理**：每一台洗衣機/烘衣機都是獨立裝置，方便分配區域與管理。
- **即時狀態對應**：
  - **待機 (Idle)**: 可供使用。
  - **使用中 (Busy)**: 執行洗程中。
  - **待取件 (Waiting for Pickup)**: 洗程結束，提醒使用者前往取衣。
  - **離線 (Offline)**: 機台維護中或網路連線中斷。
- **純英數 Entity ID**：實體 ID 統一使用店號與機器編號，穩定且易於自動化。
- **繁體中文支援**：針對台灣市場提供完整的在地化介面。
- **自定義更新頻率**：可視需求調整資料抓取間隔。

## 安裝方式

### HACS 安裝 (推薦)
1. 在 Home Assistant 中開啟 **HACS**。
2. 點選右上角三個點，選擇 **Custom repositories**。
3. 加入 URL `https://github.com/PinLin/familaundry-homeassistant` 並選擇類別 **Integration**。
4. 點選安裝並重啟 Home Assistant。

### 手動安裝
1. 下載本專案。
2. 將 `custom_components/familaundry` 資料夾複製到 Home Assistant 的 `config/custom_components/` 目錄。
3. 重啟 Home Assistant。

## 設定流程
1. 前往 **設定** > **裝置與服務** > **新增整合**。
2. 搜尋 **FamilyMart Laundry**。
3. 依照步驟選擇 **縣市** 與 **門市**。
4. 完成後，機台將會顯示在裝置清單中。

## 參與貢獻
如果您發現任何問題或有功能建議，歡迎提交 [Issue](https://github.com/PinLin/familaundry-homeassistant/issues)。

## 授權
[MIT License](LICENSE)
