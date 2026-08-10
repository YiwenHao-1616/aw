from DrissionPage import ChromiumPage, ChromiumOptions
from bs4 import BeautifulSoup
import time
import os
import sys

# ================= huisi配置区域 =================
BASE_URL = "https://orders.jiajiao169.cn/c2g/"
OUTPUT_FILE = "result_huisi.txt"
MAX_ALLOW_PAGES = 30  # 安全上限，防止死循环
# ===============================================

# 是否在 CI 环境（GitHub Actions）运行
IS_CI = os.environ.get('GITHUB_ACTIONS') == 'true' or os.environ.get('CI') == 'true'

def init_browser():
    """初始化浏览器：CI 环境用无头模式 + no-sandbox"""
    co = ChromiumOptions()
    if IS_CI:
        # GitHub Actions 是无显示器 + root 环境，必须无头 + 关闭沙箱
        co.headless(True)
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
    # Linux 上指定 Chrome 路径（ubuntu-latest 自带）
    if sys.platform.startswith('linux'):
        for p in ['/usr/bin/google-chrome-stable', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser']:
            if os.path.exists(p):
                co.set_browser_path(p)
                break
    page = ChromiumPage(co)
    return page

def get_current_page_content(page):
    """获取当前页纯文本内容"""
    try:
        time.sleep(2)
        page_html = page.html
        soup = BeautifulSoup(page_html, 'html.parser')
        for useless_tag in soup(["script", "style"]):
            useless_tag.decompose()
        pure_text = soup.get_text(separator='\n', strip=True)
        return pure_text if len(pure_text) > 100 else None
    except Exception as e:
        print(f"解析错误: {e}")
        return None

def find_next_button(page):
    """增强型查找下一页按钮：滚动+等待+多重选择器"""
    page.scroll.to_bottom()
    time.sleep(1)
    selectors = [
        'css:button[aria-label="Go to next page"]',
        'css:button.btn-next',
        'text:下一页'
    ]
    for selector in selectors:
        try:
            btn = page.wait.ele_displayed(selector, timeout=5)
            if btn:
                return btn
        except:
            continue
    return None

def start_crawl():
    print("🚀 启动浏览器，准备开始爬取...")
    browser = init_browser()
    all_full_content = []
    current_page_index = 1
    last_page_text = ""

    try:
        browser.get(BASE_URL)
        while current_page_index <= MAX_ALLOW_PAGES:
            print(f"📄 正在处理第 {current_page_index} 页...")
            page_text = get_current_page_content(browser)
            if page_text:
                if page_text == last_page_text:
                    print("🛑 检测到内容与上一页完全一致，判定已到达最后一页")
                    break
                last_page_text = page_text
                page_mark = f"\n{'='*35} 第 {current_page_index} 页 {'='*35}\n"
                all_full_content.append(page_mark + page_text)
                print(f"✅ 第 {current_page_index} 页抓取成功 (长度: {len(page_text)})")
            else:
                print(f"⚠️ 第 {current_page_index} 页内容为空")
            next_btn = find_next_button(browser)
            if not next_btn:
                print("🛑 未找到下一页按钮，结束任务")
                break
            print("👉 点击下一页...")
            try:
                next_btn.click()
            except Exception as e:
                print(f"❌ 点击失败: {e}")
                break
            time.sleep(3)
            current_page_index += 1
    except Exception as e:
        print(f"❌ 爬取过程异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        browser.quit()
    return "\n".join(all_full_content)

def save_to_local_file(content):
    save_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(save_dir, OUTPUT_FILE)
    if not content:
        print("⚠️ 警告: 未获取到有效内容，文件未生成")
        # CI 环境下生成空文件会误导后续推送，这里直接返回
        return False
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        file_size = os.path.getsize(full_path)
        print(f"🎉 成功! 文件已保存至: {full_path}")
        print(f"   文件大小: {file_size} bytes")
        return True
    except Exception as e:
        print(f"❌ 文件保存失败: {e}")
        return False

if __name__ == "__main__":
    try:
        final_result = start_crawl()
        ok = save_to_local_file(final_result)
        # 【关键】CI 环境抓取失败时应以非0退出码终止，让 workflow 失败而非静默推送空文件
        if IS_CI:
            if not ok or not final_result:
                print("❌ CI 环境：抓取无内容，以非0状态退出")
                sys.exit(1)
    except Exception as e:
        print(f"主程序错误: {e}")
        if IS_CI:
            sys.exit(1)
    finally:
        # 【关键修改】仅在本地交互环境等待回车；CI 环境直接退出，否则会卡死
        if not IS_CI:
            input("\n任务结束，按回车键退出窗口...")
