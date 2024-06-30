import requests
import yaml

def verify_https_status(check):
    url = check['url']
    expected_status = check['expected_status']

    try:
        response = requests.get(url)
        if response.status_code == expected_status:
            print(f"{url} is reachable and returns status {expected_status}")
        else:
            print(f"{url} returned status {response.status_code}, expected {expected_status}")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to {url}: {e}")

def main():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    if 'checks' in config:
        for check in config['checks']:
            verify_https_status(check)
    else:
        print("No 'checks' found in config.yaml")

if __name__ == '__main__':
    main()
