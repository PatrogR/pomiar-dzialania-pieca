import os
import csv

def get_daily_gas_reading(file_path: str, date_str: str):
    # Sprawdzenie, czy plik istnieje, jeśli nie, tworzymy pusty plik
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='') as file:
            file.write("")

    # Wczytanie istniejących odczytów do słownika
    readings = {}
    with open(file_path, 'r', newline='') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            if len(row) == 2:
                readings[row[0]] = row[1]

    # Sprawdzenie, czy odczyt dla podanej daty już istnieje
    if date_str in readings:
        print(f"Dzisiejszy odczyt już istnieje: {readings[date_str]}")
        return float(readings[date_str])

    # Pobranie odczytu od użytkownika
    user_input = input("Podaj bieżący odczyt gazomierza (Enter = 0): ").replace(',', '.')
    try:
        gazomierz_odczyt = float(user_input) if user_input.strip() else 0
    except ValueError:
        print("Błędny format liczby! Przyjęto wartość 0.")
        gazomierz_odczyt = 0.0

    # Zapisanie odczytu do słownika
    readings[date_str] = f"{gazomierz_odczyt:.3f}"
    # Posortowanie odczytów według daty
    sorted_readings = sorted(readings.items())

    # Zapisanie odczytów do pliku CSV
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(sorted_readings)

    print(f"Bieżący odczyt gazomierza zapisany: {gazomierz_odczyt:.3f}")
    return gazomierz_odczyt
