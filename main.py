from machine import Pin,ADC # type: ignore
from time import sleep
import dht # type: ignore
import requests as urequests
import requests 
import time, network,machine,onewire, ds18x20 # type: ignore

#sensor = dht.DHT22(Pin(14))
sensor = dht.DHT11(Pin(27))
soil_moisture = ADC(Pin(35))

#pins to regulate pump through driver
Pump_Pin=Pin(21,Pin.OUT)
Pump1=Pin(18,Pin.OUT)
Pump2=Pin(19,Pin.OUT)
Pump1.value(1)
Pump2.value(0)

#pins to regulate LED through driver
LED_Pin=Pin(13,Pin.OUT)
LED1=Pin(12,Pin.OUT)
LED2=Pin(14,Pin.OUT)
LED1.value(1)
LED2.value(0)

#initial dummy values
LDR_value=1000
LDR_status=0
moisture=100
pump_status=0

max_moisture=4095
soil_moisture.atten(ADC.ATTN_11DB)       #Full range: 3.3v
soil_moisture.width(ADC.WIDTH_12BIT)     #range 0 to 4095

soil_temp_sensor = ds18x20.DS18X20(onewire.OneWire(Pin(25)))
sts_devices = soil_temp_sensor.scan()
# Initialize the ADC (Analog to Digital Converter) for the LDR pin
LDR = ADC(Pin(33))
LDR.atten(ADC.ATTN_11DB)

HTTP_HEADERS = {'Content-Type': 'application/json'} 
THINGSPEAK_WRITE_API_KEY = '********' 

UPDATE_TIME_INTERVAL = 15000  # in ms 
last_update = time.ticks_ms()

ssid = 'abcd'
password = ''

def connect_wifi(ssid, password):
    #Connect to your network
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)
    while station.isconnected() == False:
        pass
    print('Connection successful')
    print(station.ifconfig())
    
def send_message(phone_number, api_key, message):
    #set your host URL
    url = 'https://api.callmebot.com/whatsapp.php?phone='+phone_number+'&text='+message+'&apikey='+api_key

    response = requests.post(url)
    #check if it was successful
    if response.status_code == 200:
        print('Success!')
    else:
        print('Error')
        print(response.text)

phone_number = '+9*********'
api_key = '********'

connect_wifi(ssid,password)
while True: 
    if time.ticks_ms() - last_update >= UPDATE_TIME_INTERVAL: 
        try:
            if LDR_value<500:#Previously led was on or off?
                LDR_value=4095-LDR.read()
                if LDR_value>500:
                    LDR_status=0
                    LED_Pin.value(0)
                    message = "LED%20has%20been%20turned%20off!%20"
                    send_message(phone_number,api_key,message)
            else:
                LDR_value=4095-LDR.read()
                if LDR_value<500:
                    LDR_status=1
                    LED_Pin.value(1)
                    message = "LED%20has%20been%20turned%20on!%20"
                    send_message(phone_number,api_key,message)
            if moisture>=50:#Previously pump was on or off?
                moisture= (max_moisture-soil_moisture.read())*100/max_moisture
                if moisture<=50:
                    Pump_Pin.value(1)
                    pump_status=1
                    message = "Water%20Pump%20has%20been%20turned%20on!%20"
                    send_message(phone_number,api_key,message)
            else:
                moisture= (max_moisture-soil_moisture.read())*100/max_moisture
                if moisture>=50:
                    Pump_Pin.value(0)
                    pump_status=0
                    message = "Water%20Pump%20has%20been%20turned%20off!%20"
                    send_message(phone_number,api_key,message)
            last_update = time.ticks_ms()
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            soil_temp_sensor.convert_temp()
            soil_temp=soil_temp_sensor.read_temp(sts_devices[0])
            print('Soil temperature : ',soil_temp,' C')
            print('Soil moisture : ',moisture)
            print(f'LDR reading: {LDR_value}')
            print('Temperature: %3.1f C' %temp)
            print('Humidity: %3.1f %%' %hum)
        except OSError as e:
            print('Failed to read sensor.')
        time.sleep(1)
        readings = {'field2':temp, 'field3':hum,'field4':pump_status,'field5':LDR_status,'field6':soil_temp} 
        request = urequests.post( 'http://api.thingspeak.com/update?api_key=' + THINGSPEAK_WRITE_API_KEY,
                                 json = readings, headers = HTTP_HEADERS )  
        request.close() 
        print(readings) 
