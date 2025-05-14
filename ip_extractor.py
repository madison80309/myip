import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import os

# 打印当前工作目录，确保路径正确
print(f"当前工作目录: {os.getcwd()}")

# 使用 webdriver_manager 自动管理 ChromeDriver
service = Service(ChromeDriverManager().install())

# 国家代码到中文的映射
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
}

# 初始化 WebDriver
def create_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")  # 如果你希望无界面模式运行
    return webdriver.Chrome(service=service, options=options)

# 用于提取网页中的IP地址
def extract_ips_from_page(page_source):
    ip_regex = r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    return re.findall(ip_regex, page_source)

def fix_ip_format(ip):
    parts = ip.split('.')
    fixed_parts = [str(int(part)) for part in parts]
    return '.'.join(fixed_parts)

def get_country_for_ip(ip):
    try:
        print(f"查询IP: {ip}")  # 打印正在查询的IP
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            country_code = data.get('country', 'Unknown')
            country_name = country_mapping.get(country_code, '未知')
            return country_code, country_name
        else:
            print(f"无法获取IP信息: {ip}，状态码: {response.status_code}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"获取IP信息时出错: {ip}，错误: {e}")
        return None, '超时'

def get_ips_from_url(url, driver):
    try:
        print(f"正在访问页面: {url}")  # 打印访问的URL
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//body")))
        time.sleep(2)

        page_source = driver.page_source
        ips = extract_ips_from_page(page_source)
        print(f"提取到的IP: {ips}")  # 打印提取到的IP地址
        fixed_ips = [fix_ip_format(ip) for ip in ips]
        print(f"修正后的IP: {fixed_ips}")  # 打印修正后的IP地址
        fixed_ips = [ip for ip in fixed_ips if ip != '87.74.4.147']
        return fixed_ips
    except Exception as e:
        print(f"访问页面时出错: {e}")
        return []

def main():
    url = 'https://www.nslookup.io/domains/ips.meizitu.net/dns-records/#cloudflare'
    ip_addresses = set()

    driver = create_driver()
    ips = get_ips_from_url(url, driver)
    ip_addresses.update(ips)

    ip_with_country = []
    for ip in ip_addresses:
        time.sleep(10)
        country_code, country_name = get_country_for_ip(ip)
        if country_code and country_name != '超时':
            ip_with_country.append(f"{ip}#{country_code}{country_name}")
        else:
            ip_with_country.append(f"{ip}#超时")

    ip_with_country.sort(key=lambda x: x.split('#')[1])

    # 明确指定文件保存路径为根目录
    ip_file_path = './ip.txt'
    ip_with_country_file_path = './ip_with_country.txt'

    # 打印保存路径调试信息
    print(f"IP 文件将保存到: {ip_file_path}")
    print(f"带国家信息的 IP 文件将保存到: {ip_with_country_file_path}")

    try:
        # 确保文件保存
        with open(ip_file_path, 'w') as file:
            for ip in ip_addresses:
                file.write(f"{ip}\n")
        print(f"IP地址已保存到 {ip_file_path}")

        if ip_with_country:
            with open(ip_with_country_file_path, 'w') as file:
                for ip_country in ip_with_country:
                    file.write(f"{ip_country}\n")
            print(f"带有国家信息的IP地址已保存到 {ip_with_country_file_path}")
        else:
            print("没有带国家信息的IP地址。")

    except Exception as e:
        print(f"保存文件时出错: {e}")

    driver.quit()

if __name__ == "__main__":
    main()
