import requests
from bs4 import BeautifulSoup
import os
import time
import re
from selenium import webdriver
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# --- 配置区域 ---
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
base_url = 'http://www.oushenwenji.net/'
forum_url = 'http://www.oushenwenji.net/forum.php'
root_save_dir = '欧神文集下载'
# ----------------

if not os.path.exists(root_save_dir):
    os.makedirs(root_save_dir)


def get_soup(url):
    """通用请求函数，增加更多请求头和处理"""
    try:
        # 添加更多请求头模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'http://www.oushenwenji.net/'
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'

        # 检查响应状态码和内容长度
        if response.status_code != 200:
            print(f"      HTTP状态码错误: {response.status_code}")
            return None

        if len(response.text) < 100:
            print(f"      响应内容过短，可能被重定向或拒绝访问")
            print(f"      响应预览: {response.text[:200]}")
            return None

        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"      [请求错误] {url}: {e}")
        return None


def get_forum_info():
    """
    获取板块信息
    返回格式: [{'name': '板块名', 'url': '链接'}, ...]
    """
    soup = get_soup(forum_url)
    if not soup:
        return []

    forums = []
    # 查找板块链接
    for link in soup.find_all('a', href=True):
        href = link['href']
        # 匹配 forum-数字-1.html 或类似的板块链接规则
        if ('forum' in href and '.html' in href) or ('mod=forumdisplay' in href):
            if not href.startswith('http'):
                full_url = base_url + href if not href.startswith('/') else base_url.rstrip('/') + href
            else:
                full_url = href

            # 提取板块名称
            name = link.text.strip()

            # 过滤无效或重复的板块（根据名字或链接去重）
            # 这里的判断逻辑是：名字不为空，且链接未被添加过
            if name and not any(f['url'] == full_url for f in forums):
                forums.append({'name': name, 'url': full_url})
                print(f"发现板块: {name} -> {full_url}")

    return forums


def get_post_links(forum_url):
    """
    获取某板块下的所有帖子链接
    """
    post_links = []

    # 提取 fid
    match = re.search(r'forum-(\d+)', forum_url)
    if not match:
        print(f"  无法解析fid，跳过翻页逻辑: {forum_url}")
        return []

    fid = match.group(1)
    page = 1
    max_pages = 50  # 安全阈值

    while page <= max_pages:
        current_url = f"{base_url}forum-{fid}-{page}.html"
        # print(f"  正在分析第 {page} 页: {current_url}") # 调试时可开启

        soup = get_soup(current_url)
        if not soup:
            break

        found_new = 0
        # 查找帖子链接 (通常 class="xst" 或在 id="threadlist" 中)
        # 这里使用比较通用的包含 thread 的链接查找
        for link in soup.find_all('a', href=True):
            href = link['href']
            # 排除回复链接，通常帖子链接是 thread-ID-1-1.html
            if 'thread' in href and '.html' in href and 'unapproved' not in href:
                if not href.startswith('http'):
                    full_url = base_url + href if not href.startswith('/') else base_url.rstrip('/') + href
                else:
                    full_url = href

                if full_url not in post_links:
                    post_links.append(full_url)
                    found_new += 1

        if found_new == 0:
            # 如果这一页没有任何新帖子，通常意味着已经超出了最大页数
            break

        # 检查是否有"下一页" (Discuz 通用 class 'nxt')
        if not soup.find('a', class_='nxt') and page > 1:
            break

        page += 1
        time.sleep(0.5)

    return post_links


def get_soup_selenium(url):
    """
    使用Selenium获取页面，可执行JavaScript
    增加视频资源处理优化
    """
    # 初始化浏览器驱动，使用无头模式（不弹出窗口）
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 无头模式，后台运行
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # 关键：禁止加载图片和视频，大幅提高加载速度
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,  # 1:允许, 2:阻止
            'plugins': 2,  # 阻止Flash
            'popups': 2,  # 阻止弹窗
            'geolocation': 2,  # 阻止地理位置
            'notifications': 2,  # 阻止通知
            'media_stream': 2,  # 阻止媒体流
            'media_stream_mic': 2,  # 阻止麦克风
            'media_stream_camera': 2,  # 阻止摄像头
            'automatic_downloads': 2,  # 阻止自动下载
        }
    }
    options.add_experimental_option('prefs', prefs)

    # 设置User-Agent
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    # 添加额外的性能优化参数
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-logging')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')

    driver = None
    try:
        driver = webdriver.Chrome(options=options)

        # 设置超时策略
        driver.set_page_load_timeout(15)  # 页面加载超时15秒
        driver.set_script_timeout(10)  # 脚本执行超时10秒

        # 使用JavaScript禁用视频预加载
        driver.execute_cdp_cmd('Network.setBlockedURLs', {
            "urls": [
                "*.mp4", "*.webm", "*.ogg", "*.avi", "*.mov", "*.flv",
                "*.m3u8", "*.mpd", "*.m4v", "*video*", "*stream*"
            ]
        })

        driver.get(url)

        # 更智能的等待策略：等待页面基本加载完成
        try:
            # 等待body元素加载
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # 额外等待一小段时间让JavaScript执行
            time.sleep(1)

        except TimeoutException:
            # 即使超时，也可能已经有部分内容了
            print("      页面加载可能较慢，但已获取部分内容")

        # 获取当前URL
        real_url = driver.current_url
        print(f"      获取到真实URL: {real_url}")

        # 获取页面源代码
        html = driver.page_source

        # 检查页面是否包含视频相关错误
        if "视频" in html and ("无法播放" in html or "加载失败" in html or "已失效" in html):
            print("      检测到视频已失效，跳过视频资源")

        return BeautifulSoup(html, 'html.parser'), real_url

    except TimeoutException as e:
        print(f"      [Selenium超时] {url}: 页面加载超时，尝试获取已有内容")
        if driver:
            try:
                # 即使超时，也尝试获取当前页面内容
                html = driver.page_source
                real_url = driver.current_url
                if html and len(html) > 1000:  # 如果有足够的内容
                    return BeautifulSoup(html, 'html.parser'), real_url
            except:
                pass
        return None, None

    except WebDriverException as e:
        print(f"      [Selenium错误] {url}: {str(e)[:100]}...")
        return None, None

    except Exception as e:
        print(f"      [Selenium异常] {url}: {e}")
        return None, None

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def is_video_post(url, soup):
    """
    判断是否是视频帖子
    """
    if not soup:
        return False

    # 检查页面内容是否包含视频关键词
    page_text = str(soup).lower()
    video_keywords = ['video', 'mp4', 'flv', 'avi', 'mov', 'wmv', 'mkv', 'webm']

    for keyword in video_keywords:
        if keyword in page_text:
            return True

    # 检查是否有视频播放器相关标签
    video_tags = soup.find_all(['video', 'iframe', 'embed', 'object'])
    if len(video_tags) > 0:
        return True

    # 检查页面标题是否包含视频相关词汇
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.text.lower()
        if any(word in title for word in ['视频', 'video', '录像', '录播']):
            return True

    return False


def download_post(post_url, save_folder):
    """
    下载帖子内容并保存为精美的HTML
    优化视频帖子处理
    """
    print(f"      正在下载: {post_url}")

    # 先尝试普通请求，判断是否是视频帖子
    soup_normal = get_soup(post_url)
    is_video = is_video_post(post_url, soup_normal)

    if is_video:
        print(f"      检测到视频帖子，跳过Selenium直接处理")
        soup = soup_normal
        real_url = post_url
    else:
        # 非视频帖子使用Selenium获取
        soup, real_url = get_soup_selenium(post_url)

        # 如果Selenium获取失败，回退到普通请求
        if not soup:
            print(f"      Selenium获取失败，使用普通请求...")
            soup = get_soup(post_url)
            real_url = post_url

    if not soup:
        print(f"      无法获取页面，跳过: {post_url}")
        return False

    # 如果是视频帖子，添加特殊标记
    if is_video:
        print(f"      注意：此帖包含视频内容，视频可能已失效")

    # 提取标题
    title = "无标题"
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.text.strip()
        # 清理标题中的Discuz标识
        if ' - Powered by Discuz!' in title:
            title = title.replace(' - Powered by Discuz!', '')
        if ' - ' in title and len(title.split(' - ')) > 1:
            title = title.split(' - ')[0]
        print(f"      提取到标题: {title[:50]}...")
    else:
        h1_tag = soup.find('h1')
        if h1_tag:
            title = h1_tag.text.strip()
            print(f"      通过h1提取标题: {title[:50]}...")
        else:
            match = re.search(r'thread-(\d+)', post_url)
            if match:
                title = f"帖子_{match.group(1)}"
                print(f"      使用URL作为标题: {title}")

    # 提取发布时间
    publish_time = "0000-00-00"
    date_patterns = [
        r'发表于 (\d{4}-\d{1,2}-\d{1,2})',
        r'(\d{4}-\d{1,2}-\d{1,2})',
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4}/\d{1,2}/\d{1,2})'
    ]

    page_text = str(soup)
    for pattern in date_patterns:
        date_match = re.search(pattern, page_text)
        if date_match:
            try:
                nums = re.findall(r'\d+', date_match.group())
                if len(nums) >= 3:
                    year, month, day = nums[0], nums[1], nums[2]
                    publish_time = f"{int(year)}-{int(month):02d}-{int(day):02d}"
                    print(f"      找到日期: {publish_time}")
                    break
            except:
                continue

    # 提取内容
    content_html = ""
    content_divs = soup.find_all(['div', 'td'], class_=['t_f', 'postmessage'])

    if content_divs:
        print(f"      找到内容区域，数量: {len(content_divs)}")
        main_content = content_divs[0]

        # 处理图片
        for img in main_content.find_all('img'):
            src = img.get('src') or img.get('file') or img.get('zoomfile')
            if src:
                if not src.startswith('http'):
                    if src.startswith('/'):
                        src = base_url.rstrip('/') + src
                    else:
                        src = base_url + src
                img['src'] = src
                img['style'] = "max-width: 100%; height: auto; margin: 10px 0;"

        content_html = str(main_content)
    else:
        # 查找其他可能的内容区域
        for elem in soup.find_all(id=re.compile('postmessage_')):
            print(f"      通过ID找到内容: {elem.get('id')}")
            content_html = str(elem)
            break

        if not content_html:
            for table in soup.find_all('table'):
                if 'post' in str(table.get('class', '')).lower():
                    print(f"      通过表格找到内容")
                    content_html = str(table)
                    break

        if not content_html:
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if len(text) > 200:
                    print(f"      通过长文本div找到内容，长度: {len(text)}")
                    content_html = str(div)
                    break

        if not content_html:
            print(f"      使用备用方案：提取页面主要内容")
            body = soup.find('body')
            if body:
                for elem in body.find_all(['script', 'style', 'iframe', 'video', 'audio']):
                    elem.decompose()
                content_html = str(body)
            else:
                content_html = f"<p>未能提取内容</p><p>原始URL: <a href='{post_url}'>{post_url}</a></p>"

    # 如果是视频帖子，在内容前添加提示
    if is_video:
        video_note = """
        <div class="video-note" style="background-color: #fff3cd; border: 1px solid #ffeaa7; 
                border-radius: 5px; padding: 15px; margin-bottom: 20px;">
            <strong>📹 视频帖子提示：</strong><br>
            此帖子包含视频内容，原始视频可能已失效或无法播放。<br>
            以下是帖子的文本内容和其他相关信息：
        </div>
        """
        content_html = video_note + content_html

    # 构建文件名
    safe_title = re.sub(r'[\\/*?:"<>|]', '', title).strip()
    if not safe_title or len(safe_title) < 2:
        match = re.search(r'thread-(\d+)', post_url)
        if match:
            safe_title = f"thread_{match.group(1)}"
        else:
            safe_title = f"post_{hash(post_url) % 10000}"

    # 如果是视频帖子，在文件名中标记
    if is_video:
        safe_title = f"[视频]{safe_title}"

    if len(safe_title) > 100:
        safe_title = safe_title[:100]

    filename = f"{publish_time}_{safe_title}.html"
    filepath = os.path.join(save_folder, filename)

    # 生成完整的HTML页面
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            font-size: 22px;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }}
        .meta {{
            color: #666;
            font-size: 14px;
            margin-bottom: 25px;
        }}
        .content {{
            font-size: 16px;
        }}
        .content img {{
            max-width: 100%;
            height: auto;
            margin: 10px 0;
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .original-link {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #888;
        }}
        .video-note {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="meta">
            <strong>发布日期:</strong> {publish_time} <br>
            <strong>原文链接:</strong> <a href="{real_url}" target="_blank">{real_url}</a>
        </div>
        <div class="content">
            {content_html}
        </div>
        <div class="original-link">
            本文档由欧神文集下载器生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""

    # 保存文件
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_template)
        print(f"      ✓ 保存成功: {filename}")
        return True
    except Exception as e:
        print(f"      ✗ 保存失败: {e}")
        # 尝试使用更简单的文件名
        try:
            simple_filename = f"{publish_time}_post_{hash(post_url) % 10000}.html"
            simple_filepath = os.path.join(save_folder, simple_filename)
            with open(simple_filepath, 'w', encoding='utf-8') as f:
                f.write(html_template)
            print(f"      ✓ 使用简化文件名保存成功: {simple_filename}")
            return True
        except:
            return False

def main():
    print("=== 欧神文集下载器 (分类版) ===")

    # 1. 获取所有板块
    print("\n正在获取板块列表...")
    forums = get_forum_info()

    if not forums:
        print("未找到任何板块，程序结束。")
        return

    print(f"共找到 {len(forums)} 个板块。")

    # 2. 遍历每个板块
    for forum in forums:
        forum_name = re.sub(r'[\\/*?:"<>|]', '', forum['name'])
        forum_url = forum['url']

        # 为该板块创建独立文件夹
        current_save_dir = os.path.join(root_save_dir, forum_name)
        if not os.path.exists(current_save_dir):
            os.makedirs(current_save_dir)

        print(f"\n{'=' * 60}")
        print(f"开始处理板块: 【{forum_name}】")
        print(f"目标文件夹: {current_save_dir}")
        print(f"板块URL: {forum_url}")

        # 3. 获取该板块下的帖子
        post_links = get_post_links(forum_url)
        # 去重
        post_links = list(set(post_links))
        print(f"共发现 {len(post_links)} 篇文章")

        print("开始下载...")

        # 4. 下载该板块的文章（带重试机制）
        success_count = 0
        for i, link in enumerate(post_links, 1):
            print(f"\n[{i}/{len(post_links)}] ", end="")

            # 尝试3次
            for retry in range(3):
                if retry > 0:
                    print(f"      第{retry + 1}次重试...")
                    time.sleep(2)  # 重试前等待

                if download_post(link, current_save_dir):
                    success_count += 1
                    break
                else:
                    if retry == 2:
                        print(f"      放弃下载: {link}")

            # 请求间隔，避免被封
            time.sleep(1)

        print(f"\n板块 【{forum_name}】 处理完成")
        print(f"成功下载: {success_count}/{len(post_links)} 篇文章")
        print(f"{'=' * 60}")

    print(f"\n全部任务完成！")
    print(f"所有文件已按板块分类保存在 '{root_save_dir}' 中。")


if __name__ == "__main__":
    main()