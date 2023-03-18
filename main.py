import requests
import config
import time
import configparser
import os


gl_last_sync_time = 0
gl_articles = []
gl_headers = {
    "user-agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 "
        "Safari/537.36",
    "authorization": f"{config.token}"
}


def get_marked_article_list_by_page(page):
    """
    分页请求有标注的文章列表（通过请求指定的智能列表 ID 实现），按照更新时间（tag 更新、笔记修改都会影响更新时间），分页请求
    :param page: 分页查询时的页码
    :return: 响应数据
    """

    # 请求 https://cubox.pro/c/api/v2/search_engine/my/aisearch/query?asc=false&orderType=3&page=1&filters=&aisearchId
    # =xxxx&archiving=false
    url = f'https://cubox.pro/c/api/v2/search_engine/my/aisearch/query'
    params = {
        'asc': 'false',
        'orderType': '3',  # 按更新时间排序
        'page': f'{page}',
        'filters': '',
        'aisearchId': f'{config.aisearchId}',
        'archiving': 'false'
    }
    response = requests.get(url, headers=gl_headers, params=params)
    if response.status_code == 200:
        json_data = response.json()
        return json_data
    pass


def get_marked_article_list():
    """
    增量请求有标注的文章列表（通过请求指定的智能列表 ID 实现），按照更新时间（tag 更新、笔记修改都会影响更新时间），分页请求
    """
    page = 1

    # 循环请求到最后一页
    while True:
        json_data = get_marked_article_list_by_page(page)
        page_count = json_data.get('pageCount')

        # 处理响应数据，获取文章列表
        article_list = json_data.get('data')
        is_break_by_last_sync_time = False
        for article in article_list:
            article_update_time = article.get('updateTime')
            # '2023-02-27T11:11:00:192+08:00' 转换为时间戳
            article_update_time = int(time.mktime(time.strptime(article_update_time, "%Y-%m-%dT%H:%M:%S:%f%z")))

            # 请求下来的数据的更新时间早于之前同步过的数据，退出循环
            if article_update_time <= gl_last_sync_time:
                is_break_by_last_sync_time = True
                break

            gl_articles.append(article)

        # 请求下来的数据的更新时间早于之前同步过的数据，退出循环
        if is_break_by_last_sync_time:
            break

        # 大于最后一页，退出循环
        page += 1
        if page > page_count:
            break


def get_mark_list_by_page(page):
    """
    请求标注数据，分页请求
    :param page: 分页请求时的页码
    :return: 标注数据
    """

    # 请求 https://cubox.pro/c/api/v2/mark/list/query?asc=false&orderType=3&page=1&filters=&colorTypes=
    url = f'https://cubox.pro/c/api/v2/mark/list/query'
    params = {
        'asc': 'false',
        'orderType': '3',  # 按更新时间排序
        'page': f'{page}',
        'filters': '',
        'colorTypes': ''
    }
    response = requests.get(url, headers=gl_headers, params=params)
    if response.status_code == 200:
        json_data = response.json()
        return json_data
    pass


def add_mark_to_article(article_id, mark):
    for article in gl_articles:
        if article.get('userSearchEngineID') == article_id:
            article['marks'].append(mark)
            break


def get_mark_list():
    page = 1

    # 循环请求到最后一页
    while True:
        json_data = get_mark_list_by_page(page)
        page_count = json_data.get('pageCount')

        # 处理响应数据，获取文章列表
        mark_list = json_data.get('data')
        is_break_by_last_sync_time = False
        for mark in mark_list:
            mark_update_time = mark.get('updateTime')
            # '2023-02-27T11:11:00:192+08:00' 转换为时间戳
            mark_update_time = int(time.mktime(time.strptime(mark_update_time, "%Y-%m-%dT%H:%M:%S:%f%z")))
            # 请求下来的数据的更新时间早于之前同步过的数据，退出循环
            if mark_update_time <= gl_last_sync_time:
                is_break_by_last_sync_time = True
                break

            add_mark_to_article(mark.get('engineID'), mark)

        # 请求下来的数据的更新时间早于之前同步过的数据，退出循环
        if is_break_by_last_sync_time:
            break

        # 大于最后一页，退出循环
        page += 1
        if page > page_count:
            break


def update_last_sync_time():
    """
    更新上一次同步时间
    """

    if len(gl_articles) > 0:
        last_sync_time = gl_articles[0].get('updateTime')
        update_config('last_sync_time', last_sync_time)


def update_config(key, value):
    config_parser = configparser.ConfigParser()
    config_path = os.path.join(config.sync_directory, 'config.md')
    config_parser.read(config_path, encoding='utf-8')
    config_parser.set('config', key, value)
    config_parser.write(open(config_path, 'w', encoding='utf-8'))


def is_image_note(mark):
    """
    判断标注的是否为图片
    :return: 是否为图片
    """
    if mark.get('endParentTagName') == 'IMG':
        return True


def write_to_file():
    """
    将文章列表写入文件
    """

    # 创建文件夹
    if not os.path.exists(config.sync_directory):
        os.makedirs(config.sync_directory)

    # 写入文件
    for article in gl_articles:
        file_path = os.path.join(config.sync_directory, article.get('title').replace('/', ' ') + '.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            tags_content = ' '.join(['#' + tag.get('name') for tag in article.get('tags')])
            mark_content = ''
            for mark in article.get('marks'):
                if not is_image_note(mark):
                    mark_content += config.mark_template.format(highlight=mark.get('text').replace('\n', '\n> '),
                                                                tags=tags_content, note_text=mark.get('noteText'))
                    mark_content += '\n'
                else:
                    mark_content += config.mark_template.format(highlight='![](' + mark.get('url') + ')',
                                                                tags=tags_content, note_text=mark.get('noteText'))
                    mark_content += '\n'

            desc = article.get('description')
            desc = desc.replace('\n', ' ') if desc is not None else ''
            article_content = config.article_template.format(article_id=article.get('userSearchEngineID'), title=article.get('title'), description=desc.replace('\n', ' '), url=article.get('targetURL'), created=article.get('createTime'), updated=article.get('updateTime'), marks=mark_content)
            f.write(article_content)


def read_config():
    """
    读取配置文件
    """

    # 如果配置文件不存在，创建配置文件
    if not os.path.exists(config.sync_directory):
        os.makedirs(config.sync_directory)
    if not os.path.exists(os.path.join(config.sync_directory, 'config.md')):
        with open(os.path.join(config.sync_directory, 'config.md'), 'w', encoding='utf-8') as f:
            f.write('[config]')
    config_parser = configparser.ConfigParser()
    config_parser.read(os.path.join(config.sync_directory, 'config.md'), encoding='utf-8')
    global gl_last_sync_time
    last_sync_time = config_parser.get('config', 'last_sync_time', fallback='0')
    gl_last_sync_time = 0 if last_sync_time == '0' \
        else int(time.mktime(time.strptime(last_sync_time, "%Y-%m-%dT%H:%M:%S:%f%z")))


if __name__ == '__main__':
    read_config()
    get_marked_article_list()
    get_mark_list()
    write_to_file()
    update_last_sync_time()
    print(f"update {len(gl_articles)} article")


