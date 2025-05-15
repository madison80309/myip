import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import os

# 使用 webdriver_manager 自动管理 ChromeDriver
service = Service(ChromeDriverManager().install())

# 从 country.txt 加载国家代码到中文名称的映射
def load_country_mapping():
    country_mapping = {}
    try:
        with open('country.txt', 'r', encoding='utf-8') as file:
            content = file.read().strip()
            items = content.split(',')
            for i in range(0, len(items), 2):  # 每两个值一组
                if i + 1 < len(items):
                    country_code = items[i].strip()
                    country_name = items[i + 1].strip()
                    country_mapping[country_code] = country_name
    except FileNotFoundError:
        print("未找到 country.txt 文件，使用默认的国家映射。")
        # 如果没有 country.txt 文件，则使用默认的国家映射
        country_mapping = {
            "US": "美国",
            "CN": "中国",
            "JP": "日本",
            "IN": "印度",
            "GB": "英国",
            "DE": "德国",
            "HK": "香港",
            "FR": "法国",
            "CA": "加拿大",
            "AU": "澳大利亚",
            "BR": "巴西",
            # 可以根据需要添加更多的映射
        }
    return country_mapping

# 初始化 WebDriver
def create_driver():
    # 设置 ChromeOptions
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 无头模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # 设置一个唯一的用户数据目录，防止冲突
    user_data_dir = "/tmp/chrome_user_data"
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    options.add_argument(f'--user-data-dir={user_data_dir}')

    # 使用 webdriver_manager 安装的 chromedriver
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

# 用于提取网页中的IP地址
def extract_ips_from_page(page_source):
    ip_regex = r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    return re.findall(ip_regex, page_source)

# 用于修正IP地址的格式，去掉每部分的前导零
def fix_ip_format(ip):
    parts = ip.split('.')
    fixed_parts = [str(int(part)) for part in parts]  # 转换每个部分为整数，再转换回字符串
    return '.'.join(fixed_parts)

# 获取IP地址的国家信息
def get_country_for_ip(ip, country_mapping):
    try:
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=5)  # 设置超时为5秒
        if response.status_code == 200:
            data = response.json()
            country_code = data.get('country', 'Unknown')  # 获取国家信息的代码
            country_name = country_mapping.get(country_code, '未知')  # 获取中文国家名
            return country_code, country_name
        else:
            print(f"无法获取IP地址 {ip} 的国家信息，状态码: {response.status_code}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"获取IP地址 {ip} 国家信息时发生错误或超时: {e}")
        return None, '超时'

# 用于访问网页并提取IP地址
def get_ips_from_url(url, driver):
    try:
        driver.get(url)
        # 显式等待页面加载完成
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//body")))

        time.sleep(2)  # 确保页面内容完全加载
        
        page_source = driver.page_source
        ips = extract_ips_from_page(page_source)
        
        # 调试：打印提取的IP
        print(f"提取到的IP地址: {ips}")
        
        # 修正每个IP地址的格式
        fixed_ips = [fix_ip_format(ip) for ip in ips]
        
        # 去除指定IP地址 '87.74.4.147'
        fixed_ips = [ip for ip in fixed_ips if ip != '87.74.4.147']
        
        if fixed_ips:
            print(f"修正后的IP地址（排除87.74.4.147）：{fixed_ips}")
            return fixed_ips
        else:
            print(f"没有在 {url} 中提取到有效IP地址")
            return []
    except Exception as e:
        print(f"访问网站 {url} 时发生错误: {e}")
        return []

def main():
    # 从 domain.txt 文件读取域名，并按逗号分隔
    with open('domain.txt', 'r') as file:
        domains_line = file.read().strip()  # 读取文件并去除首尾空白符
    domains = domains_line.split(',')  # 使用逗号分隔域名

    # 加载国家映射
    country_mapping = load_country_mapping()

    # 用于存储提取的IP地址
    ip_addresses = set()  # 使用 set 自动去重

    # 初始化 WebDriver
    driver = create_driver()

    # 对每个域名执行 IP 提取
    for domain in domains:
        domain = domain.strip()  # 去除每个域名的首尾空格
        if domain:  # 如果是空行则跳过
            print(f"正在处理域名: {domain}")
            # 直接使用域名构造 URL，不需要加前缀
            url = f'https://www.nslookup.io/domains/{domain}/dns-records/#cloudflare'
            url = f'https://www.itdog.cn/tcping/ips.meizitu.net:443'
            ips = get_ips_from_url(url, driver)
            ip_addresses.update(ips)  # 将提取的IP地址添加到集合中

    # 打印IP地址集合，确保有数据
    print(f"收集到的IP地址: {ip_addresses}")

    # 获取每个IP的国家信息并保存
    ip_with_country = []  # 确保初始化变量
    for ip in ip_addresses:
        # 添加 2秒的时间间隔
        time.sleep(2)  # 等待2秒，控制API请求频率
        
        country_code, country_name = get_country_for_ip(ip, country_mapping)
        
        # 如果API返回国家信息
        if country_code and country_name != '超时':
            ip_with_country.append(f"{ip}#{country_code}{country_name}")
        else:
            # 处理API超时或出错的情况
            ip_with_country.append(f"{ip}#超时")

    # 按国家名称排序
    ip_with_country.sort(key=lambda x: x.split('#')[1])  # 根据国家名排序
    
    # 将IP地址（仅IP）保存到ip.txt
    if ip_addresses:
        with open('ip.txt', 'w') as file:
            for ip in ip_addresses:
                file.write(f"{ip}\n")
        print(f"提取到的IP地址已保存到 ip.txt 文件中。")
    else:
        print("没有提取到任何IP地址。")

    # 将排序后的IP和国家信息保存到ip_with_country.txt
    if ip_with_country:
        with open('ip_with_country.txt', 'w') as file:
            for ip_country in ip_with_country:
                file.write(f"{ip_country}\n")
        print(f"提取到的IP地址和国家信息已按国家排序并保存到 ip_with_country.txt 文件中。")
    else:
        print("没有提取到任何有效IP地址。")

    # 关闭WebDriver
    driver.quit()

if __name__ == "__main__":
    main()
