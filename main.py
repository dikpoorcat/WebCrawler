import requests
from bs4 import BeautifulSoup
import os
import time

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 网站基础URL
base_url = 'http://oushenwenji.net/'
forum_url = 'http://oushenwenji.net/forum.php'

# 创建一个文件夹来保存文章
save_dir = '欧神文集下载'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)


def get_soup(url):
    """获取URL的BeautifulSoup对象"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"访问 {url} 失败: {e}")
        return None


def get_forum_links():
    """获取论坛所有板块的链接"""
    soup = get_soup(forum_url)
    if not soup:
        return []

    forum_links = []
    # 查找板块链接 - 根据实际页面结构调整选择器
    # 这里示例查找所有可能是板块链接的a标签
    for link in soup.find_all('a', href=True):
        href = link['href']
        # 根据你的页面结构，可能需要调整这个条件
        if 'forum' in href and '.html' in href: # mod=forumdisplay
            full_url = base_url + href if not href.startswith('http') else href
            if full_url not in forum_links:
                forum_links.append(full_url)
                print(f"找到板块: {link.text.strip()} - {full_url}")

    return forum_links


def get_post_links(forum_url):
    """获取一个板块中所有帖子的链接"""
    post_links = []
    page = 1

    while True:
        # 分页处理 - 根据Discuz的分页规则
        if page == 1:
            current_url = forum_url
        else:
            current_url = f"{forum_url}&page={page}"

        soup = get_soup(current_url)
        if not soup:
            break

        # 查找帖子链接 - 根据实际页面结构调整
        found_new = False
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'thread' in href and '.html' in href:
                full_url = base_url + href if not href.startswith('http') else href
                if full_url not in post_links:
                    post_links.append(full_url)
                    found_new = True

        # 如果没有找到新帖子，或者达到一定页数限制，就停止
        if not found_new or page >= 20:  # 限制最多爬20页
            break

        page += 1
        time.sleep(1)  # 礼貌性延迟，避免给服务器造成压力

    return post_links


def download_post(post_url, index):
    """下载单个帖子的内容"""
    soup = get_soup(post_url)
    if not soup:
        return

    # 提取帖子标题
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else f"帖子_{index}"

    # 清理文件名中的非法字符
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    if not safe_title:
        safe_title = f"帖子_{index}"

    # 提取主要内容
    content_divs = soup.find_all(['div', 'td'], class_=['t_f', 'postmessage'])
    content = ""

    if content_divs:
        for div in content_divs:
            content += div.text.strip() + "\n\n"
    else:
        # 如果没有找到特定class的内容，提取所有段落
        paragraphs = soup.find_all('p')
        if paragraphs:
            for p in paragraphs:
                content += p.text.strip() + "\n\n"
        else:
            content = soup.get_text()

    # 保存到文件
    filename = os.path.join(save_dir, f"{index:04d}_{safe_title[:50]}.txt")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"标题: {title}\n")
        f.write(f"链接: {post_url}\n")
        f.write(f"下载时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(content)

    print(f"已保存: {filename}")
    return True


def main():
    print("开始下载欧神文集...")

    # 1. 获取所有板块链接
    print("\n1. 获取论坛板块...")
    forum_links = get_forum_links()

    if not forum_links:
        print("未找到板块链接，尝试直接获取帖子...")
        forum_links = [forum_url]

    # 2. 遍历每个板块，获取帖子链接
    print("\n2. 获取所有帖子链接...")
    all_post_links = []

    for i, forum_link in enumerate(forum_links, 1):
        print(f"\n处理板块 {i}/{len(forum_links)}: {forum_link}")
        post_links = get_post_links(forum_link)
        all_post_links.extend(post_links)
        print(f"找到 {len(post_links)} 个帖子")
        time.sleep(2)

    # 去重
    all_post_links = list(set(all_post_links))
    print(f"\n共找到 {len(all_post_links)} 个唯一帖子")

    # 3. 下载每个帖子
    print("\n3. 开始下载帖子内容...")
    successful = 0

    for i, post_link in enumerate(all_post_links, 1):
        print(f"\n下载帖子 {i}/{len(all_post_links)}: {post_link}")
        if download_post(post_link, i):
            successful += 1
        time.sleep(1.5)  # 礼貌性延迟

    print(f"\n下载完成！成功下载 {successful}/{len(all_post_links)} 个帖子")
    print(f"文件保存在: {os.path.abspath(save_dir)}")


if __name__ == "__main__":
    main()