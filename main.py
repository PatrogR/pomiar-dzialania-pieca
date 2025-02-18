import os
import requests
import time
import csv
from datetime import datetime
from configparser import ConfigParser
from multiprocessing import Process

# Ścieżka do pliku konfiguracyjnego
CONFIG_FILE_PATH = 'setup.ini'


def load_config():
    """
    Wczytuje konfigurację z pliku setup.ini
    """
    config = ConfigParser()
    config.read(CONFIG_FILE_PATH)

    csv_folder = config.get('Settings', 'CSV_FOLDER')  # Folder zapisu plików CSV
    delay_value = int(config.get('Settings', 'DELAY'))  # Opóźnienie przed zapisem "turn on"
    threshold_value = int(config.get('Settings', 'THRESHOLD_VALUE'))  # Próg mocy dla przełączania

    # Pobranie adresu sensora i interwału czasowego
    sensor_data = config.get('Address', 'POWER_SENSOR_ADDRESS')
    url, time_interval = sensor_data.split(',')
    sensor_instance = SensorItem('power-sensor-data', url, int(time_interval))

    return csv_folder, sensor_instance, delay_value, threshold_value


class Sensor:
    """
    Klasa reprezentująca pojedynczy sensor
    """

    def __init__(self, type, value, trend, state):
        self.type = type
        self.value = value
        self.trend = trend
        self.state = state


class PowerSensor:
    """
    Klasa reprezentująca czujnik mocy zawierający listę sensorów
    """

    def __init__(self, sensors):
        self.sensors = sensors


class SensorItem:
    """
    Klasa przechowująca informacje o sensorze, takie jak nazwa pliku, URL oraz interwał czasowy
    """

    def __init__(self, file_name, url, time_interval):
        self.file_name = file_name
        self.url = url
        self.time_interval = int(time_interval)


def format_timestamp():
    """
    Zwraca sformatowany znacznik czasu
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_to_csv(data, csv_filename):
    """
    Zapisuje dane do pliku CSV
    """
    current_time = format_timestamp()
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=";")
        if file.tell() == 0:
            writer.writerow(['Datetime', 'State'])  # Nagłówek pliku, jeśli jest pusty
        writer.writerow([current_time, data])


def deserialize_json_to_object(url):
    """
    Pobiera dane JSON z podanego adresu URL i zwraca wartość mocy
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        sensor_value = data["sensors"][0]["value"]
        return sensor_value
    except requests.exceptions.RequestException as e:
        print(f"Błąd podczas żądania HTTP: {e}")
        return None
    except (ValueError, KeyError, IndexError) as e:
        print(f"Błąd przetwarzania danych JSON: {e}")
        return None


def monitor_power_threshold(url, csv_folder, file_name, delay_value, threshold_value):
    """
    Monitoruje wartość mocy i zapisuje "turn on" oraz "turn off" po spełnieniu określonych warunków
    """
    above_threshold = False  # Flaga określająca czy wartość przekroczyła próg
    start_time = None  # Czas rozpoczęcia przekroczenia progu
    recorded_on = False  # Flaga określająca, czy "turn on" zostało zapisane
    recorded_off = False  # Flaga określająca, czy "turn off" zostało zapisane
    last_power_value = None  # Zmienna do przechowywania ostatniej wartości mocy wydrukowanej na konsoli

    while True:
        power_value = deserialize_json_to_object(url)
        current_date = datetime.now().strftime("%Y-%m-%d")
        csv_filename = os.path.join(csv_folder, f"{file_name}_{current_date}.csv")

        if power_value is not None:
            # Sprawdzanie, czy wartość mocy różni się od poprzedniej o co najmniej 20W
            if last_power_value is None or abs(power_value - last_power_value) >= 20:
                print(f"{datetime.now().strftime("%H:%M:%S")} -> {power_value}W")  # Wyświetlanie bieżącej mocy
                last_power_value = power_value  # Aktualizowanie ostatniej wartości mocy

            if power_value > threshold_value:
                if not above_threshold:
                    start_time = time.time()
                    above_threshold = True
                    recorded_on = False  # Resetowanie flagi "turn on"
                elif time.time() - start_time >= delay_value and not recorded_on:
                    write_to_csv('Turn on', csv_filename)
                    recorded_on = True
                    recorded_off = False  # Resetowanie flagi "turn off"
            elif power_value < threshold_value - 5:
                if above_threshold and not recorded_off:
                    write_to_csv('Turn off', csv_filename)
                    recorded_off = True
                    recorded_on = False  # Resetowanie flagi "turn on"
                    above_threshold = False  # Resetowanie stanu progu

        time.sleep(1)


def main():
    """
    Główna funkcja programu - inicjalizuje konfigurację oraz uruchamia monitorowanie w osobnym procesie
    """
    csv_folder, sensor, delay_value, threshold_value = load_config()

    if not os.path.exists(csv_folder):
        os.makedirs(csv_folder)  # Tworzy folder, jeśli nie istnieje

    Process(target=monitor_power_threshold,
            args=(sensor.url, csv_folder, sensor.file_name, delay_value, threshold_value)).start()


if __name__ == "__main__":
    main()