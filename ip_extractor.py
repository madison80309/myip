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
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            country_code = data.get('country', 'Unknown')
            country_name = country_mapping.get(country_code, '未知')
            return country_code, country_name
        else:
            return None, None
    except requests.exceptions.RequestException as e:
        return None, '超时'

def get_ips_from_url(url, driver):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//body")))
        time.sleep(2)

        page_source = driver.page_source
        ips = extract_ips_from_page(page_source)
        fixed_ips = [fix_ip_format(ip) for ip in ips]
        fixed_ips = [ip for ip in fixed_ips if ip != '87.74.4.147']
        return fixed_ips
    except Exception as e:
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

    ip_file_path = '/home/runner/work/myip/myip/ip.txt'
    ip_with_country_file_path = '/home/runner/work/myip/myip/ip_with_country.txt'

    try:
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
