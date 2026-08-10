from DrissionPage import ChromiumPage
from bs4 import BeautifulSoup
import time
import os

# ================= huisi配置区域 =================
BASE_URL = "https://orders.jiajiao169.cn/c2g/"
OUTPUT_FILE = "result_huisi.txt"
MAX_ALLOW_PAGES = 30  # 安全上限，防止死循环
# ===========================================

def init_browser():
    """初始化浏览器"""
    page = ChromiumPage()
    # 若想观察过程，取消下面这行的注释
    # page.set.headless(False)
    return page

def get_current_page_content(page):
    """获取当前页纯文本内容"""
    try:
        time.sleep(2)  # 等待JS渲染
        page_html = page.html
        soup = BeautifulSoup(page_html, 'html.parser')
        
        # 过滤无用标签
        for useless_tag in soup(["script", "style"]):
            useless_tag.decompose()
            
        pure_text = soup.get_text(separator='\n', strip=True)
        return pure_text if len(pure_text) > 100 else None
    except Exception as e:
        print(f"解析错误: {e}")
        return None

def find_next_button(page):
    """增强型查找下一页按钮：滚动+等待+多重选择器"""
    # 1. 滚动到底部，触发懒加载
    page.scroll.to_bottom()
    time.sleep(1)
    
    # 2. 显式等待按钮出现 (最多等5秒)
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
            
            # 1. 获取内容
            page_text = get_current_page_content(browser)
            
            if page_text:
                # 【关键】内容去重：如果和上一页一样，说明没翻过去或到顶了
                if page_text == last_page_text:
                    print("🛑 检测到内容与上一页完全一致，判定已到达最后一页")
                    break
                
                last_page_text = page_text
                page_mark = f"\n{'='*35} 第 {current_page_index} 页 {'='*35}\n"
                all_full_content.append(page_mark + page_text)
                print(f"✅ 第 {current_page_index} 页抓取成功 (长度: {len(page_text)})")
            else:
                print(f"⚠️ 第 {current_page_index} 页内容为空")
            
            # 2. 寻找并点击下一页
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
            
            # 3. 等待新页面加载
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
    """保存到脚本所在目录，确保双击运行时也能找到文件"""
    # 获取脚本所在的绝对路径
    save_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(save_dir, OUTPUT_FILE)
    
    if not content:
        print("⚠️ 警告: 未获取到有效内容，文件未生成")
        return
        
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        file_size = os.path.getsize(full_path)
        print(f"🎉 成功! 文件已保存至: {full_path}")
        print(f"   文件大小: {file_size} bytes")
    except Exception as e:
        print(f"❌ 文件保存失败: {e}")

if __name__ == "__main__":
    try:
        final_result = start_crawl()
        save_to_local_file(final_result)
    except Exception as e:
        print(f"主程序错误: {e}")
    finally:
        # 【关键】防止双击运行时窗口闪退，按回车才关闭
        input("\n任务结束，按回车键退出窗口...")
