import requests
import time
import random
import re
import sys
import threading
import colorama
from colorama import init, Fore, Style
import httpx
from captcha_solver import solve_recaptcha, get_task_result

init(autoreset=True)

DEFAULT_PASSWORD = 'Hesap oluştururken kullanmasını istediginiz şifre'
CAPSOLVER_API_KEY = 'capsolver keyiniz'#capsolver.com
KOPEECHKA_API_KEY = 'kopeechka keyiniz' #kopeechka.store
SITE_KEY = '6Ld_HZ0lAAAAAG0--R4Ix2kT7fCGN_onQdtUYH-4'
SITE_URL = 'https://auth.trendyol.com'

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'application-id': '1',
    'content-type': 'application/json;charset=UTF-8',
    'culture': 'tr-TR',
    'storefront-id': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'origin': 'https://auth.trendyol.com',
    'referer': 'https://auth.trendyol.com/static/fragment?application-id=1&storefront-id=1&culture=tr-TR&language=tr&debug=false',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'priority': 'u=1, i',
}

proxy_list = open("proxies.txt", "r").readlines()

def save_account_info(email, password):
    with open('saves.txt', 'a') as file:
        file.write(f"{email}:{password}\n")

def get_mail(token, domain):
    try:
        response = httpx.get(f"https://api.kopeechka.store/mailbox-get-email?site=www.trendyol.com&mail_type=OUTLOOK&token={token}&password=0&regex=&subject=&investor=&soft=&type=json&api=2.0")
        if response.status_code == 200:
            req = response.json()
            if req["status"] == "OK":
                return req["mail"], req["id"], response.text
            elif req["status"] == "ERROR":
                if req["value"] == "BAD_TOKEN":
                    sys.exit("Invalid Kopeechka API key")
                raise Exception(req["value"])
        else:
            raise Exception(f"Failed to fetch email: {response.text}")
    except Exception as e:
        raise Exception(f"Error fetching email: {str(e)}")

def get_verification_code(email_id, token):
    email_printed = True
    while True:
        try:
            response = httpx.get(f"https://api.kopeechka.store/mailbox-get-message?full=1&id={email_id}&token={token}")
            if response.status_code == 200:
                req = response.json()
                if req["status"] == "OK":
                    full_message = req["fullmessage"]
                    if not email_printed:
                        email_printed = True
                    code = re.search(r'<strong>(\d+)</strong>', full_message)
                    if code:
                        verification_code = code.group(1).strip()
                        print(f"Verification code: {verification_code}")
                        return verification_code
                    else:
                        raise Exception("Verification code not found in the email message.")
                elif req["status"] == "ERROR":
                    raise Exception(req["value"])
            else:
                raise Exception(f"Failed to fetch verification code: {response.text}")
        except Exception as e:
            print(f"Error fetching verification code: {str(e)}")
            time.sleep(1)

def register_account(mail, email_id, token):
    try:
        proxy = random.choice(proxy_list)
        proxies = {'http': 'http://' + proxy.strip(), 'https': 'http://' + proxy.strip()}

        task_id = solve_recaptcha(CAPSOLVER_API_KEY, SITE_KEY, SITE_URL)
        if task_id:
            print(f"\033[92mTask ID: {task_id}")
            
            g_recaptcha_response = get_task_result(CAPSOLVER_API_KEY, task_id)

            json_data = {
                'email': mail,
                'password': DEFAULT_PASSWORD,
                'genderId': 1,
                'captchaToken': g_recaptcha_response,
                'marketingEmailsAuthorized': True,
                'newCoPrivacyStatementForTYChecked': True,
                'conditionOfMembershipApproved': True,
                'protectionOfPersonalDataApproved': True,
                'otpCode': None,
            }

            response = requests.post('https://auth.trendyol.com/v2/signup', headers=headers, json=json_data, proxies=proxies)

            if response.status_code == 200:
                print(f"{Fore.GREEN}Trendyol kayıt işlemi başarılı! E-posta: {mail}, Şifre: {DEFAULT_PASSWORD}")
                save_account_info(mail, DEFAULT_PASSWORD)
            elif response.status_code == 428 and "E-posta doğrulaması gerekli." in response.text:
                print("\033[92mE-posta doğrulaması gerekli. Bekleniyor...")

                verification_code = get_verification_code(email_id, token)
                json_data['otpCode'] = verification_code

                response = requests.post('https://auth.trendyol.com/v2/signup', headers=headers, json=json_data, proxies=proxies)

                if response.status_code == 200:
                    print(f"{Fore.GREEN}Trendyol kayıt işlemi başarılı! E-posta: {mail}, Şifre: {DEFAULT_PASSWORD}, {response.text}")
                    save_account_info(mail, DEFAULT_PASSWORD)
                else:
                    print(f"Trendyol kayıt işlemi başarısız. Status code: {response.status_code}, Response: {response.text}")
            else:
                print(f"Trendyol kayıt işlemi başarısız. Status code: {response.status_code}, Response: {response.text}")
        else:
            print("Failed to get task ID.")
    except Exception as e:
        print(f"Error: {str(e)}")
    return False, None

def main():
    print(Fore.MAGENTA + "                        Trendyol Account Gen | discord.gg/clown |github/kuzey1337\n\n\n")

    try:
        num_threads = int(input("\033[95mKaç thread çalıştırmak istiyorsunuz? "))
    except ValueError:
        print("Geçersiz sayı.")
        return

    if num_threads <= 0:
        print("En az bir thread çalıştırmalısınız.")
        return

    accounts = []
    try:
        for _ in range(num_threads):
            mail, email_id, first_response = get_mail(KOPEECHKA_API_KEY, "www.trendyol.com")
            if mail:
                accounts.append((mail, email_id))
            else:
                print(f"Hata: E-posta alınamadı.")
                return
    except Exception as e:
        print(f"Hata: {str(e)}")
        return

    threads = []
    for mail, email_id in accounts:
        thread = threading.Thread(target=register_account, args=(mail, email_id, KOPEECHKA_API_KEY))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print(f"{Fore.GREEN}{num_threads} adet hesap başarıyla oluşturuldu.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
