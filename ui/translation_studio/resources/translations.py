# Traditional Chinese UI strings
# 唯一使用者可見語言：繁體中文

class Strings:
    # Application
    APP_TITLE = "NTPE 翻譯工作室"

    # Navigation
    NAV_HOME = "首頁"
    NAV_PROJECT = "專案"

    # Home Page
    HOME_WELCOME = "歡迎使用 NTPE 翻譯工作室"
    HOME_DESCRIPTION = "專業的小說翻譯工具，支援 TXT 與 EPUB 格式"
    HOME_ACTION_IMPORT_TXT = "匯入 TXT"
    HOME_ACTION_IMPORT_EPUB = "匯入 EPUB"
    HOME_ACTION_NEW_PROJECT = "新增專案"
    HOME_ACTION_OPEN_PROJECT = "開啟專案"

    # TXT Import
    TXT_IMPORT_DIALOG_TITLE = "選擇 TXT 檔案"
    TXT_FILE_FILTER = "文字檔案 (*.txt)"
    TXT_IMPORT_SUCCESS_TITLE = "匯入成功"
    TXT_IMPORT_SUCCESS_MSG = "書名：{title}\n來源檔案：{source}\n內容長度：{chars} 字元\n編碼：{encoding}"
    TXT_IMPORT_FAILED_TITLE = "匯入失敗"
    TXT_IMPORT_FAILED_MSG = "狀態：{status}\n警告：{warnings}"
    TXT_IMPORT_ERROR_TITLE = "匯入錯誤"
    TXT_IMPORT_ERROR_MSG = "發生錯誤：{error}"
    UNKNOWN = "未知"
    NO_DETAILS = "無詳細資訊"

    # EPUB Import
    EPUB_IMPORT_DIALOG_TITLE = "選擇 EPUB 檔案"
    EPUB_FILE_FILTER = "EPUB 電子書 (*.epub)"
    EPUB_IMPORT_SUCCESS_TITLE = "匯入成功"
    EPUB_IMPORT_SUCCESS_MSG = "書名：{title}\n來源檔案：{source}\n章節數：{chapters}\n內容長度：{chars} 字元"
    EPUB_IMPORT_PARTIAL_TITLE = "部分匯入"
    EPUB_IMPORT_PARTIAL_MSG = "EPUB 部分解析完成，但有部分內容無法完全解析。\n書名：{title}\n來源檔案：{source}\n解析章節數：{chapters}\n內容長度：{chars} 字元\n警告：{warnings}"
    EPUB_IMPORT_FAILED_TITLE = "匯入失敗"
    EPUB_IMPORT_FAILED_MSG = "狀態：{status}\n警告：{warnings}"
    EPUB_IMPORT_ERROR_TITLE = "匯入錯誤"
    EPUB_IMPORT_ERROR_MSG = "發生錯誤：{error}"

    # Project Page
    PROJECT_TITLE = "專案管理"
    PROJECT_LIST_EMPTY = "尚無專案，請從首頁建立新專案"
    PROJECT_COLUMN_NAME = "專案名稱"
    PROJECT_COLUMN_SOURCE = "來源檔案"
    PROJECT_COLUMN_STATUS = "狀態"
    PROJECT_COLUMN_PROGRESS = "進度"
    PROJECT_ACTION_DELETE = "刪除"
    PROJECT_ACTION_RESUME = "繼續"
    PROJECT_ACTION_VIEW = "檢視"
    PROJECT_ACTION_PREVIEW = "預覽內容"

    # Preview
    PREVIEW_TITLE = "內容預覽"
    PREVIEW_TXT_LABEL = "原文內容"
    PREVIEW_EPUB_LABEL = "章節內容"
    PREVIEW_NO_CONTENT = "無可預覽的內容"
    PREVIEW_PARTIAL_WARNING = "⚠ 部分匯入：部分內容無法完全解析"
    PREVIEW_WARNINGS = "警告：{warnings}"
    PREVIEW_TRUNCATED = "... (內容過長，僅顯示前 {chars} 字元)"
    PREVIEW_FULL = "完整內容"
    PREVIEW_CLOSE = "關閉"

    # Common
    BTN_BACK = "返回"
    BTN_CLOSE = "關閉"
    BTN_CANCEL = "取消"
    BTN_CONFIRM = "確認"
    BTN_SAVE = "儲存"
    BTN_OPEN = "開啟"
    BTN_BROWSE = "瀏覽"

    # Status
    STATUS_READY = "就緒"
    STATUS_LOADING = "載入中..."
    STATUS_ERROR = "發生錯誤"

    # Translation
    PROJECT_ACTION_TRANSLATE = "開始翻譯"
    TRANSLATION_STATUS_PREPARING = "準備翻譯"
    TRANSLATION_STATUS_RUNNING = "翻譯中"
    TRANSLATION_STATUS_COMPLETED = "翻譯完成"
    TRANSLATION_STATUS_FAILED = "翻譯失敗"
    TRANSLATION_STATUS_INCOMPLETE = "翻譯未完成"
    TRANSLATION_PROGRESS_FORMAT = "已完成 {completed} / {total}"
    TRANSLATION_OUTPUT_LABEL = "輸出位置"
    TRANSLATION_CHUNKS_SUCCESSFUL = "成功區塊：{successful} / {total}"
    TRANSLATION_MODEL_LABEL = "翻譯模型"
    TRANSLATION_TARGET_LANG_LABEL = "目標語言"
    TRANSLATION_SOURCE_FILE_LABEL = "來源檔案"
    TRANSLATION_NOT_SUPPORTED_EPUB = "EPUB 專案暫不支援直接啟動翻譯"
    TRANSLATION_NO_VALID_SOURCE = "無有效 TXT 來源，無法啟動翻譯"
    TRANSLATION_ALREADY_RUNNING = "翻譯已在進行中"
    TRANSLATION_ERROR_PREFIX = "翻譯錯誤："

    # Messages
    MSG_CONFIRM_DELETE = "確定要刪除此專案嗎？此操作無法復原。"
    MSG_CONFIRM_CLOSE = "確定要關閉應用程式嗎？"
    MSG_FILE_NOT_FOUND = "找不到指定的檔案。"
    MSG_INVALID_FORMAT = "不支援的檔案格式。"

    # Placeholders
    PLACEHOLDER_NOT_IMPLEMENTED = "此功能尚未實作，將在後續版本提供。"
    PLACEHOLDER_COMING_SOON = "即將推出"


# 字串對照表（用於檢查無英文標籤）
EN_TO_ZH = {
    "Import": "匯入",
    "Export": "匯出",
    "Configure": "設定",
    "Preview": "預覽",
    "Translate": "翻譯",
    "Retry": "重試",
    "Settings": "設定",
    "Home": "首頁",
    "Project": "專案",
    "Start": "開始",
    "Stop": "停止",
    "Pause": "暫停",
    "Resume": "繼續",
    "Delete": "刪除",
    "Edit": "編輯",
    "Save": "儲存",
    "Cancel": "取消",
    "OK": "確定",
    "Yes": "是",
    "No": "否",
    "Close": "關閉",
    "Back": "返回",
    "Next": "下一步",
    "Previous": "上一步",
    "Finish": "完成",
    "Loading": "載入中",
    "Ready": "就緒",
    "Error": "錯誤",
    "Warning": "警告",
    "Info": "資訊",
    "Success": "成功",
    "Failed": "失敗",
    "Pending": "待處理",
    "Running": "執行中",
    "Completed": "已完成",
    "File": "檔案",
    "Folder": "資料夾",
    "Name": "名稱",
    "Status": "狀態",
    "Progress": "進度",
    "Language": "語言",
    "Model": "模型",
    "Provider": "供應商",
    "Profile": "設定檔",
    "Chunk Size": "區塊大小",
    "Timeout": "逾時",
    "Resume": "續傳",
    "Overwrite": "覆寫",
    "Validate": "驗證",
    "Browse": "瀏覽",
    "Choose": "選擇",
    "Select": "選取",
    "Open": "開啟",
    "New": "新增",
    "Create": "建立",
    "Remove": "移除",
    "Clear": "清除",
    "Reset": "重設",
    "Apply": "套用",
    "Default": "預設",
    "Advanced": "進階",
    "Basic": "基本",
    "General": "一般",
    "Appearance": "外觀",
    "Behavior": "行為",
    "Shortcuts": "快捷鍵",
    "About": "關於",
    "Help": "說明",
    "Documentation": "文件",
    "License": "授權",
    "Version": "版本",
    "Update": "更新",
    "Check": "檢查",
    "Download": "下載",
    "Install": "安裝",
    "Uninstall": "解除安裝",
    "Restart": "重新啟動",
    "Exit": "離開",
    "Quit": "退出",
}
