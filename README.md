# Fami Laundry（全家自助洗衣）Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/PinLin/familaundry-homeassistant.svg?style=flat-square)](https://github.com/PinLin/familaundry-homeassistant/releases)
[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://github.com/hacs/integration)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

將全家自助洗衣（Fami 自助洗衣）的機台狀態整合到 Home Assistant，提供即時的洗烘進度監控。

## 功能特色
- **裝置化管理**：每一台洗衣機/烘衣機都是獨立裝置，方便分配區域與管理。
- **即時狀態對應**：
  - **待機（Idle）**：可供使用。
  - **使用中（Busy）**：執行洗程中。
  - **待取件（Waiting for Pickup）**：洗程結束，提醒使用者前往取衣。
- **自訂更新頻率**：可視需求調整資料抓取間隔。
- **手動更新服務**：提供 `familaundry.update`，可更新全部門市或指定 `store_ids`。

## 安裝方式

### HACS 安裝（推薦）

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PinLin&repository=familaundry-homeassistant&category=integration)

1. 在 Home Assistant 中開啟 **HACS**。
2. 點選右上角三個點，選擇 **Custom repositories**。
3. 加入 URL `https://github.com/PinLin/familaundry-homeassistant` 並選擇類別 **Integration**。
4. 點選安裝並重啟 Home Assistant。

### 手動安裝
1. 下載本專案。
2. 將 `custom_components/familaundry` 資料夾複製到 Home Assistant 的 `config/custom_components/` 目錄。
3. 重啟 Home Assistant。

## 設定流程

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=familaundry)

1. 前往**設定** > **裝置與服務** > **新增整合**。
2. 搜尋 **Fami Laundry**。
3. 依照步驟選擇**縣市**與**門市**。
4. 完成後，機台將會顯示在裝置清單中。

## 裝置與屬性

- 每台機器會建立為獨立裝置。
- 裝置型號欄位會顯示門市 ID，例如 `021112`。
- 實體屬性會顯示 `store_id`，可用於手動更新服務。

## 服務

### `familaundry.update`

手動更新 Fami Laundry 機台狀態。

```yaml
service: familaundry.update
data:
  store_ids:
    - "021112"
```

`store_ids` 留空時會更新所有已設定的門市。

## 疑難排解

### 機台狀態長時間沒有更新
1. 確認 Home Assistant 的網路可以正常連到外部。Fami Laundry API 偶爾會短暫回應錯誤，本整合會自動重試；若連續多次失敗，會在**設定** > **修復**中顯示通知。
2. 在**設定** > **裝置與服務** > **Fami Laundry**將更新間隔調短，重新拉一次資料。
3. 透過 `familaundry.update` 服務手動觸發更新。

### 想看更詳細的紀錄
在 `configuration.yaml` 加入：

```yaml
logger:
  logs:
    custom_components.familaundry: debug
```

重啟後，相關紀錄會出現在 Home Assistant 的系統紀錄中。

### 提交 Issue
請在**設定** > **裝置與服務** > **Fami Laundry** > 三個點 > **下載診斷資料**取得 JSON，連同 Home Assistant 版本與重現步驟一起附上，能大幅縮短排查時間。

## 移除整合

1. 前往**設定** > **裝置與服務**。
2. 點選 **Fami Laundry** 整合卡片。
3. 點選右上角三個點 > **刪除**。
4. 若不再需要本整合的程式碼，可在**HACS**中將其移除，或手動刪除 `config/custom_components/familaundry/` 資料夾。

## 免責聲明

本整合為非官方、社群維護的專案，與全家便利商店股份有限公司無任何關係。資料來源為 Fami 自助洗衣公開的網頁 API；若該 API 異動或停止服務，本整合可能無法繼續運作。

## 授權
[MIT License](LICENSE)
