import network
from time import sleep
import urequests

try:
    import config
except ImportError:
    raise RuntimeError("Config file not found. Please upload config.py with Wi-Fi credentials.")



def connect_to_wifi():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    for _ in range(30):  # Try for 15 seconds
        if wlan.isconnected():
            print('Connected to Wi-Fi')
            print('IP address:', wlan.ifconfig()[0])
            return
        sleep(0.5)
    
    raise RuntimeError('Failed to connect to Wi-Fi')



# Function to query an API
def query_api(url):
    try:
        response = urequests.get(url)
        print('Response status:', response.status_code)
        print('Response text:', response.text)
        response.close()
    except Exception as e:
        print('Failed to query API:', e)

# Main code
if __name__ == "__main__":
    connect_to_wifi()
    query_api('https://jsonplaceholder.typicode.com/todos/1')