import network
import time
import dht
#from wifi_lib import conecta
from machine import Pin
from umqtt.simple import MQTTClient
import _thread


def conecta(ssid,senha):
    import network
    import time

    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, senha)
    
    for t in range(50):
        if station.isconnected():
            print('conectado!')
            break
        time.sleep(0.1)
    return station

# Configurações MQTT
BROKER = "broker.mqttdashboard.com"
PORT = 1883
USER = ''
PASSWORD = ''
CLIENT_ID = "AS2-CAIOJCC-WOKWI"
CLIENT_ID_1 = "AS2-CAIOJCC-WOKWI1"
Tumidade = b"as2/caiojcc/umidade"
Tmovimento = b"as2/caiojcc/movimento"
Ttemperatura = b"as2/caiojcc/temperatura"
Tbutton = b"as2/caiojcc/button"

global movimento
global umidade
global temperatura
global trava
global trava_desl

movimento = 0
umidade = 0
temperatura = 0
trava = False
trava_desl = False

# Configurações de pinos
led = Pin(2, Pin.OUT)
sensor_umidade = dht.DHT22(Pin(15))
pir_sensor = Pin(13, Pin.IN)

def modo_manual(topico, msg):
    global trava
    global trava_desl

    if msg.decode() == 'liga':
        print('Botão ligado manualmente! Modo Automático Desligado !')
        trava = True
        trava_desl = False
        led.value(1)

    elif msg.decode() == 'desliga':
        trava = False
        trava_desl = True
        led.value(0)
        print('Botão desligado manualmente! Modo Automático Desligado')

    elif msg.decode() == 'religar':
        trava = False
        trava_desl = False
        print('Modo Automático Religado!')

def sensor(): # Funfando
    global movimento
    global umidade
    global temperatura

    while True:
        # Lê o sensor de umidade
        sensor_umidade.measure()
        umidade = sensor_umidade.humidity()

        movimento = pir_sensor.value()

        # Lê o sensor de temperatura
        temperatura = sensor_umidade.temperature()
        time.sleep(2)


def envia():
    global trava
    global trava_desl

    station = conecta('Wokwi-GUEST', '')
    if not station.isconnected():
        print('Falha na conexão !')
    else:
        print('WIFI Conectado!')
        print('Conectando Broker MQTT HIVE')
        client = MQTTClient(CLIENT_ID,
        BROKER,
        PORT,
        USER,
        PASSWORD)
        client.connect()
        client.set_callback(modo_manual)
        client.subscribe(Tbutton)
        print('broker conectado')

        while True:
            # Envia os dados ao broker MQTT
            client.publish(Tumidade, str(umidade).encode())
            client.publish(Ttemperatura, str(temperatura).encode())

            if (movimento == 1 or umidade >= 100) and not trava and not trava_desl:
                led.value(1) # Liga o LED
                print('Movimento ou Humidade detectada ! LED ligado')
                movimento_str = 'Movimento Detectado!'
                client.publish(Tmovimento, str(movimento_str).encode())
                time.sleep(1)

            elif (movimento == 1 or umidade >= 100) and trava:
                print('Movimento ou Humidade detectada ! LED TRAVADO!')
                movimento_str = 'Movimento Detectado!'
                client.publish(Tmovimento, str(movimento_str).encode())
                time.sleep(1)

            elif movimento == 0 and not trava:
                led.value(0) # Desliga o LED
                movimento_str = 'Movimento não Detectado!'
                client.publish(Tmovimento, str(movimento_str).encode())

            elif movimento == 0 and trava:
                movimento_str = 'Movimento não Detectado!'
                client.publish(Tmovimento, str(movimento_str).encode())



            client.check_msg()  # Verifica se há mensagens recebidas
            time.sleep(2)        




_thread.start_new_thread(envia, ())  # Inicia a thread para escutar e publicar dados
time.sleep(10)
_thread.start_new_thread(sensor, ())  # Inicia o modo automático

