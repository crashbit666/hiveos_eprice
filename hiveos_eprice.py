import argparse
import subprocess
from datetime import datetime
import json
import requests


def get_arguments():
    # Detecta las opciones pasadas por linea de comandos
    """
        Opciones obligatorias:
            maxprice        Precio máximo KW/h aceptado para que el rig esté minando. ex: hiveos_powersafe 0.2564

        Actualmente los valores opcionales son:
            -h              Para ayuda
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("maxprice", help="Precio máximo KW/h antes de que se apague el rig. Ex: 0.2400", type=float)
    args = parser.parse_args()
    return args


def get_price_per_hour():
    token = "84df043582208624ed92672a280bc9862df5b00220b2645f53edcd0d58c3015d"
    url = 'https://api.esios.ree.es/indicators/1001'
    headers = {'Accept': 'application/json; application/vnd.esios-api-v2+json', 'Content-Type': 'application/json',
               'Host': 'api.esios.ree.es', 'Authorization': 'Token token=' + token}

    pkw = []

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        json_data = json.loads(response.text)

        vals = json_data['indicator']['values']

        prices = [x['value'] for x in vals]

        hour = 0
        x = 0

        for price in prices:
            if vals[x].get('geo_id') == 8741:
                pkw.append(round(price/1000, 4))
                hour += 1
            x += 1
    else:
        pkw = "Error de conexión a la base de datos de precios de la luz"
    return pkw


def get_time():
    date = datetime.now()
    hour = date.strftime('%H')
    return hour


def check_if_miner_is_active():
    # Test if miner is active
    try:
        subprocess.check_output(["ps -aux | grep [m]iner-run"], shell=True).decode()
        return True
    except subprocess.CalledProcessError:
        return False


def miner_shutdown(now_price, max_price):
    print("El precio actual de la electricidad es de {} KW/h y has especificado un precio máximo de {}".format
          (now_price, max_price))
    print("Stopping mining rig . . .")
    try:
        shutdown = subprocess.check_output(['/hive/bin/miner', 'stop'], shell=True)
        print(shutdown)
    except subprocess.CalledProcessError as e:
        print(e.output)


def miner_start():
    print("Start minng ...")
    try:
        start = subprocess.check_output(['/hive/bin/miner', 'start'], shell=True)
        print(start)
    except subprocess.CalledProcessError as e:
        print(e.output)


def main():
    # Recoge los argumentos pasados al iniciar el programa y asigna variables
    args = get_arguments()
    max_price = args.maxprice
    print(max_price)

    # Detecta la hora actual
    hour = get_time()

    # Recoge los precios del día
    price = get_price_per_hour()

    # Detecta el precio de la hora actual
    now_price = float(price[int(hour)])

    if check_if_miner_is_active() and now_price > max_price:
        miner_shutdown(now_price, max_price)
    elif not check_if_miner_is_active() and now_price < max_price:
        miner_start()


if __name__ == '__main__':
    main()
