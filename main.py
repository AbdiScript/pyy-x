import requests
response = requests.get('https://api64.ipify.org?format=json')
ip_address = response.json().get('ip')

print(f"Public IP Address: {ip_address}")

from fake_useragent import UserAgent
import requests

ua = UserAgent(browsers=['edge', 'chrome'])
# ua.random
# print(ua.chrome)
header = {'User-Agent':str(ua.random)}
header = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/120.0.2210.126 Version/17.0 Mobile/15E148 Safari/604.1',

    }
# print(header)
url = "https://api.digikala.com/v1/categories/mens-apparel/search/?page=1"
htmlContent = requests.get(url, headers=header, timeout=5)
print(htmlContent)
# print(htmlContent.text)
