from main import download_post

links = [
    # 'http://www.oushenwenji.net/thread-41939-1-1.html',
    # 'http://www.oushenwenji.net/thread-42422-1-1.html',
    # 'http://www.oushenwenji.net/thread-42243-1-1.html',
    # 'http://www.oushenwenji.net/thread-42707-1-1.html',
    # 'http://www.oushenwenji.net/thread-42762-1-1.html',
    # 'http://www.oushenwenji.net/thread-42191-1-1.html',
    # 'http://www.oushenwenji.net/thread-43797-1-1.html',
    # 'http://www.oushenwenji.net/thread-42530-1-1.html',
    # 'http://www.oushenwenji.net/thread-42190-1-1.html',
    # 'http://www.oushenwenji.net/thread-44194-1-1.html',
    # 'http://www.oushenwenji.net/thread-43234-1-1.html',
    # 'http://www.oushenwenji.net/thread-42425-1-1.html',
    # 'http://www.oushenwenji.net/thread-42147-1-1.html',
    # 'http://www.oushenwenji.net/thread-42277-1-1.html',
    # 'http://www.oushenwenji.net/thread-42201-1-1.html',
    # 'http://www.oushenwenji.net/thread-42194-1-1.html',
    # 'http://www.oushenwenji.net/thread-42526-1-1.html',
    # 'http://www.oushenwenji.net/thread-42801-1-1.html',
    # 'http://www.oushenwenji.net/thread-42203-1-1.html',
    # 'http://www.oushenwenji.net/thread-42649-1-1.html',
    # 'http://www.oushenwenji.net/thread-42730-1-1.html',
    # 'http://www.oushenwenji.net/thread-42889-1-1.html',

    # 'http://www.oushenwenji.net/thread-42913-1-1.html',
    # 'http://www.oushenwenji.net/thread-43625-1-1.html',
    # 'http://www.oushenwenji.net/thread-43165-1-1.html',
    # 'http://www.oushenwenji.net/thread-44337-1-1.html',
    # 'http://www.oushenwenji.net/thread-42674-1-1.html',
    # 'http://www.oushenwenji.net/thread-44301-1-1.html',
    # 'http://www.oushenwenji.net/thread-43478-1-1.html',
    #
    'http://www.oushenwenji.net/thread-42770-1-1.html',
    'http://www.oushenwenji.net/thread-43792-1-1.html',
    'http://www.oushenwenji.net/thread-43566-1-1.html',
]

for link in links:
    # download_post(link, 'D:/GitHub/WebCrawler/欧神文集下载/欧神文集')
    # download_post(link, 'D:/GitHub/WebCrawler/欧神文集下载/欧神小密圈')
    download_post(link, 'D:/GitHub/WebCrawler/欧神文集下载/欧神朋友圈')
