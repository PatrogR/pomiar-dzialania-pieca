import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import matplotlib.dates as mdates
import os
import tracemalloc
from datetime import datetime, timedelta, time, date
from matplotlib.animation import FuncAnimation
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.table import Table
# from setproctitle import setproctitle

# setproctitle("Buderus")

plt.rcParams['axes.unicode_minus'] = False

pid = os.getpid()
print(f"Aktulany PID: {pid}")
#tracemalloc.start()

font_manager.fontManager.addfont('arialn.ttf')
font_manager.fontManager.addfont('arialnb.ttf')
font_manager.fontManager.addfont('arialnbi.ttf')
font_manager.fontManager.addfont('arialn.ttf')
# print(font_manager.findSystemFonts(fontpaths=None, fontext='ttf'))
# print(font_manager.findfont("Arial Narrow"))

# Zmienna, która będzie domyślną datą (bieżąca data)
default_date = date.today().strftime('%Y-%m-%d')
#today_date = '2024-03-26'

# Możesz wprowadzić własną datę lub użyć domyślnej daty
today_date = input(f"Wprowadź datę w formacie 'rrrr-mm-dd' (naciśnij Enter, aby użyć domyślnej daty {default_date}): ")

# Jeśli użytkownik nie wprowadzi daty, użyj domyślnej daty
if not today_date:
    today_date = default_date

global end_time
end_time = None
end_time_input = input(f"Wprowadź godzinę w formacie 'hh:mm' ) (Naciśnij Enter, aby nie ograniczać czasu):")
if not end_time_input:
    end_time = None
else:
    end_time = f'{today_date} {end_time_input}'
#end_time = None
#end_time = f'{today_date} {end_time}'

def update_end_time():
    global end_time
    # Obliczenie czasu: obecny czas minus 1 doba
    one_day_ago = datetime.now() - timedelta(days=1)
    # Formatowanie do ciągu znaków
    end_time = one_day_ago.strftime('%Y-%m-%d %H:%M:%S')
    
# Dan wejściowe gazu
#gas_flow = 0.049357895
#gas_flow = 0.045684211
gas_flow = 0.0444825752817695
gas_cost = 0.3429732
gas_energy = 11.583
internet_delay = 0
#gazomierz_odczyt = 10878.885

# Pobranie bieżącego odczytu gazomierza od użytkownika
user_input = input("Podaj bieżący odczyt gazomierza (Enter = 0): ").replace(',','.')

# Konwersja wartości, jeśli użytkownik coś wpisał
try:
    gazomierz_odczyt = float(user_input) if user_input.strip() else 0
except ValueError:
    print("Błędny format liczby! Przyjęto wartość 0.")
    gazomierz_odczyt = 0.0

print(f"Bieżący odczyt gazomierza: {gazomierz_odczyt:.3f}")

# Dane centralnego ogrzewania
# Naleźy dodać warunki do anazliy
reduce_hours_days = 5
reduce_hours_weekend = 6
heat_hours_days = 24 - reduce_hours_days
heat_hours_weekend = 24 - reduce_hours_weekend

# Sprawdzenie dnia tygodnia
today_date_date = datetime.strptime(today_date, '%Y-%m-%d').date()
if today_date_date.weekday() < 5: # Poniedziałek do piątku (0-4)
    time_day_start = '0:00'
    reduction_minutes = 0
else:
    time_day_start = '0:00'
    reduction_minutes = 0


csv_file_path1 = f'csv_saves/power-sensor-data_{today_date}.csv'
csv_file_path2 = f'csv_saves/air_sensor_data_{today_date}.csv'
csv_file_path3 = f'csv_saves/co_sensor_data_{today_date}.csv'
csv_file_path4 = 'IFTTT Status.csv'

# Jeśli plik nie istnieje, tworzę go i dodaję nagłówki
if not os.path.exists(csv_file_path1):
    print(f"Plik {csv_file_path1} nie istnieje. Tworzę nowy plik...")
    with open(csv_file_path1, 'w') as file:
        file.write('Datetime;State\n')  # Nagłówki dostosuj do swoich danych
        file.write(f'{today_date} 00:00:00;Turn off\n') # Pierwszy wpis

# Alternative dates
#csv_file_path1 = f'Buderus_2024-03-20.csv'
#csv_file_path2 = f'csv_saves/air_sensor_data_2024-03-20.csv'
#csv_file_path3 = f'csv_saves/co_sensor_data_2024-03-20.csv'
#csv_file_path4 = 'IFTTT Status.csv'

#temporary_bar = None  # Przechowuje tymczasowy słupek
avg_turn_on_time = 0
avg_turn_off_time = 0

#last_datetime = datetime.now() - timedelta(days=1)  # Initial value for last_datetime
#last_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
#last_datetime = datetime(2024, 3, 20, 0, 0, 0)
last_datetime = datetime.strptime(today_date, '%Y-%m-%d') - timedelta(days=1)
total_on_time = 0  # Initialize total_on_time
total_off_time = 0 # Initillize total_off_time
turn_on_count = 0
turn_off_count = 0
avg_turn_on_time = 0
avg_turn_off_time = 0
formatted_avg_turn_on_time = 0
formatted_avg_turn_off_time = 0
last_entry = 0
previous_heat = None
previous_heat_time = None

def parse_date(date_strings):
    return pd.to_datetime(date_strings, format='%Y-%m-%d %H:%M:%S')

def read_and_process_data(csv_file):
    global end_time
    data = pd.read_csv(csv_file, sep=';', dtype={'Datetime': 'str', 'State': 'str'})
    data['Datetime'] = parse_date(data['Datetime'])
    data.columns = ['Datetime', 'State']
    # Jeśli end_time jest podany, filtrowanie do tej godziny
    if end_time is not None:
        # Zakładając, że end_time jest już odpowiednio sformatowanym stringiem daty
        end_time = pd.to_datetime(end_time)
        data = data[data['Datetime'] <= end_time]
    return data

def read_and_process_temperature_air_data(csv_file):
    global end_time
    #Wczytywanie danych temperatury z pliku CSV
    data = pd.read_csv(csv_file, sep=';', parse_dates=['Timestamp'], index_col='Timestamp', dtype={'Temperature (Celsius)': 'float'})
    # Nie ma potrzeby zmieniać nazw kolumn, jeśli są one już odpowiednio nazwane w pliku CSV
    if end_time is not None:
        end_time = pd.to_datetime(end_time)
        data = data.loc[data.index <= end_time]
    return data

def read_and_process_temperature_co_data(csv_file):
    global end_time
    #Wczytywanie danych temperatury z pliku CSV
    data = pd.read_csv(csv_file, sep=';', parse_dates=['Timestamp'], index_col='Timestamp', dtype={'Temperature (Celsius)': 'float'})
    # Nie ma potrzeby zmieniać nazw kolumn, jeśli są one już odpowiednio nazwane w pliku CSV
    if end_time is not None:
        end_time = pd.to_datetime(end_time)
        data = data.loc[data.index <= end_time]
    return data

    # Definicja nowej funkcji do odczytu fazy kotła
def read_boiler_phase(csv_file):
    data = pd.read_csv(csv_file, sep=';')  # Zakładam separator przecinkowy
    last_phase = data['Phase'].iloc[-1]  # Odczytanie ostatniej wartości z kolumny 'Phase'
    return last_phase

# Aktualizacja funkcji temporary_bar, aby używać pauza_minuty jako wysokości słupka
def temporary_bar(ax, last_entry, pauza_minuty, last_state):
    #print(f"Liczba elementów przed usunięciem: {len(ax.patches)}")
    # Usuwanie poprzedniego tymczasowego słupka
    temporary_bars = [bar for bar in ax.patches if hasattr(bar, 'is_temporary') and getattr(bar, 'is_temporary')]
    for bar in temporary_bars:
        bar.remove()
    #print(f"Liczba elementów po usunięciu: {len(ax.patches)}")
    
    # Określenie koloru na podstawie stanu kotła
    color = 'lightcoral' if last_state == 'Turn on' else 'lightskyblue'
    
    # Rysowanie nowego tymczasowego słupka z wysokością pauza_minuty
    temp_bar = ax.bar(last_entry, pauza_minuty, width=0.002, color=color, align='edge')
    setattr(temp_bar[0], 'is_temporary', True)  # Oznaczenie słupka jako tymczasowego

# Funkcja do zapisywania wykresu
def save_plot_if_time():
    # Pobieranie bieżącej daty i czasu
    now = datetime.now()
    current_time = now.time()
    
    # Określenie przedziału czasowego
    start_time = time(23, 59, 0)
    end_time = time(23, 59, 11)
    #start_time = time(21, 17, 0)
    #end_time = time(21, 17, 11)

    # Sprawdzenie, czy bieżący czas znajduje się w przedziale
    if start_time <= current_time <= end_time:
        # Tworzenie nazwy pliku z bieżącą datą
        # filename = now.strftime('wykresy/wykres_%Y-%m-%d_%H-%M-%S.png')
        filename = now.strftime('wykresy/wykres_%Y-%m-%d.png')
        plt.savefig(filename)
        print(f"Wykres został zapisany jako {filename}.")


def make_format(current, other):
    # Data bazowa Excela
    base_date = datetime(1899, 12, 30)

    def format_coord(x, y):
        # Konwersja x (format Excela) na datę i czas
        date_time = base_date + timedelta(days=x)
        # Formatowanie czasu do HH:MM
        time_str = date_time.strftime('%H:%M')

        # Konwersja współrzędnych do formatu wyświetlania dla osi current
        display_coord = current.transData.transform((x, y))
        inv = other.transData.inverted()
        # Konwersja z powrotem do współrzędnych danych z perspektywy other ax
        ax_coord = inv.transform(display_coord)

        # Oba zestawy współrzędnych muszą mieć przekonwertowaną współrzędną X
        coords = [(time_str, ax_coord[1]), (time_str, y)]

        return ('Hot Water/Time: {:<40}    Air: {:<}'
                .format(*['({0}, {1:.0f})'.format(x, y) for x, y in coords]))
    return format_coord

fig, ax1 = plt.subplots(figsize=(21, 6))
ax2 = ax1.twinx()
table_axis = fig.add_axes([0.945, 0.10, 0.06, 0.9]) # Left, bottom, width, height
table_axis.axis('off') # Ukrycie osi

ax2.format_coord = make_format(ax2, ax1)

def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'


def setup_plot():
    plt.rcParams['font.family'] = 'Arial Narrow' # W sumie to nie działa
    plt.rcParams['font.weight'] = 'bold' # To teź nie działa
    #start_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_datetime = datetime.strptime(today_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(days=1)
    ax1.set_xlim(start_datetime, end_datetime)
    ax1.set_ylim(0, 70)
    ax2.set_ylim(-10.0, 25.0)
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax1.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0, 60, 5)))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.grid(which='major', linestyle='-', linewidth='0.5', color='lightgray')
    ax1.grid(which='minor', linestyle=':', linewidth='0.5', color='#EEEEEE')
    ax1.yaxis.set_major_locator(plt.MultipleLocator(5))
    ax1.yaxis.set_minor_locator(plt.MultipleLocator(1))
    plt.subplots_adjust(left=0.0216, right=0.930, top=0.95, bottom=0.05)

    # Ustawienie czcionki dla osi wykresu
    font_props = FontProperties(family='Arial Narrow', size=12, style='normal', weight='bold')

    for label in ax1.get_xticklabels() + ax1.get_yticklabels() + ax2.get_yticklabels():
        label.set_fontproperties(font_props)

    #Ustawienie czcionki dla etykiet osi
    #ax1.set_xlabel('Oś X', fontproperties=font_props)
    #ax1.set_ylabel('Oś Y', fontproperties=font_props)
    #ax2.set_ylabel('Oś Y2', fontproperties=font_props)

setup_plot()

def format_time(time_in_minutes):
    minutes = int(time_in_minutes)
    seconds = int((time_in_minutes - minutes) * 60)
    return f"{minutes:02d}:{seconds:02d}"

def licz_obiekty_na_wykresie(ax):
    liczba_obiektow = {
        'linie': len(ax.lines),
        'teksty': len(ax.texts),
        'słupki': len(ax.patches),  # Słupki z bar() są traktowane jako "patches"
        # Dodaj więcej typów obiektów wg potrzeb
    }
    return liczba_obiektow

global line_on, line_off
line_on, line_off = None, None
avg_turn_off_text = None
avg_turn_on_text = None
last_heat = None
last_heat_time = None
text01 = None
text02 = None
text03 = None
text04 = None
text05 = None

temperature_co_data = read_and_process_temperature_co_data(csv_file_path3)
line_co, = ax1.plot(temperature_co_data.index, temperature_co_data['Temperature (Celsius)'], color='brown', label='CO')
temperature_air_data = read_and_process_temperature_air_data(csv_file_path2)
line_air, = ax2.plot(temperature_air_data.index, temperature_air_data['Temperature (Celsius)'], color='orange', label='Air')



def analyze_temperature_data(data):
    heats = []  # Lista do przechowywania wartości temperatury spełniających warunek
    heat_times = []  # Lista do przechowywania odpowiadających czasów
    heat_numbers = [] # Lista do przechowywania numerów porządkowych
    last_heat = None
    last_heat_time = None
    for i in range(len(data) - 6):  # Iterujemy do przedostatniego pomiaru, aby mieć zestaw 6 pomiarów
        A1, A2, A3, A4, A5, A6, A7 = data.iloc[i:i+7]['Temperature (Celsius)']  # Wybieramy 6 kolejnych pomiarów
        times = data.iloc[i:i+7].index  # Czas pomiaru dla wybranych 6 pomiarów
        # Sprawdzamy warunek, czy wszystkie zmienne są niepuste i czy A5 jest większe lub równe A6
        if all(x is not None for x in [A1, A2, A3, A4, A5, A6, A7]) and A1 < A2 < A3 < A4 < A5 >= A6 >= A7:
            heats.append(A5)  # Dodajemy wartość temperatury spełniającą warunek do listy
            heat_times.append(times[4])  # Dodajemy odpowiadający czas do listy
            heat_numbers.append(len(heats)) # Dodajemy numer porządkowy do listy
            last_heat = A5
            last_heat_time = times[4]  # Czas odpowiadający temperaturze A5
    return last_heat, last_heat_time, heats, heat_times, heat_numbers

# Przykładowe użycie
#csv_file_path = 'nazwa_pliku.csv'
#temperature_data = read_and_process_temperature_co_data(csv_file_path)
last_heat, last_heat_time, heats, heat_times, heat_numbers = analyze_temperature_data(temperature_co_data)
previous_heat_time = last_heat_time
previous_heat = last_heat
#print("Ostatni szczyt temperatury:", last_heat)
#print("Czas ostatniego szczytu temperatury:", last_heat_time)
for heat, time1 in zip(heats, heat_times):
    print(time1.strftime("%H:%M"),",","{:.1f}".format(heat))


# Funkcja do aktualizacji tabeli
def update_table(heats, heat_times, heat_numbers, table_axis):
    # Usuń poprzednią tabelę, jeśli istnieje
    for child in ax2.get_children():
        if isinstance(child, Table):
            child.remove()
    # Przygotowanie danych do tabeli
    table_data = [['#', 'Time', 'Temp']] # Inicjalizacja pustej tabeli
    for heat_numbers, heat, time1 in zip(heat_numbers[-34:], heats[-34:], heat_times[-34:]):
        table_data.append([heat_numbers, time1.strftime("%H:%M"), '{:.1f}'.format(heat)])
           
    # Rysowanie nowej tabeli
    plt.rcParams['font.family'] = 'Arial Narrow'
    plt.rcParams['font.weight'] = 'bold'
    table = table_axis.table(cellText=table_data, loc='upper left', cellLoc='center', rowLoc='center', colWidths=[0.2, 0.3, 0.3], edges='closed')
    
    # Wyrównanie
    cellDict = table.get_celld()
    for cell in cellDict:
        #print(cell)
        cellDict[cell].set_height(0.03)

    # Kolorowanie   
    for k, cell in table._cells.items():
        cell.set_edgecolor('lightgray')
        if k[0] == 0 or k[1] < 0:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor('red')
        else:
            cell.set_facecolor(['#F5F5F5', '#D3D3D3'][k[0] % 2])    
    plt.draw()
    
update_table(heats, heat_times, heat_numbers, table_axis)

def update(frame):  
    global last_datetime, total_on_time, total_off_time, turn_on_count, turn_off_count
    global avg_turn_on_time, avg_turn_off_time, line_on, line_off
    global formatted_avg_turn_on_time, formatted_avg_turn_off_time, avg_turn_off_text, avg_turn_on_text
    global text01, text02, text03, text04, text05
    global last_temperature_air, last_timestamp_air, last_temperature_co, last_timestamp_co, last_heat, last_heat_time, previous_heat, previous_heat_time
    global Boiler_phase
    global end_time

    # Aktualizuj end_time tylko jeśli end_time nie jest None
    if end_time is not None:
        update_end_time()

    # Inicjalizacja zmiennych statystycznych
    #turn_on_count = 0
    #turn_off_count = 0
    total_on_count = 0
    total_off_count = 0
    total_count = 0

    # Odczytanie i aktualizacja fazy kotła z pliku CSV
    Boiler_Phase = read_boiler_phase(csv_file_path4)

    data = read_and_process_data(csv_file_path1)
    data = data[data['Datetime'] > last_datetime].reset_index(drop=True)
    temperature_air_data = read_and_process_temperature_air_data(csv_file_path2)
    temperature_air_data_filtered = temperature_air_data.between_time(time_day_start, '23:59')
    line_air.set_data(temperature_air_data.index, temperature_air_data['Temperature (Celsius)'])
    temperature_co_data = read_and_process_temperature_co_data(csv_file_path3)
    temperature_co_data_filtered = temperature_co_data.between_time(time_day_start, '23:59')
    temperature_co_data_filtered2 = temperature_co_data.tail(720)
    temperature_co_data_filtered3 = temperature_co_data.tail(1440)
    temperature_co_data_filtered4 = temperature_co_data_filtered3.iloc[:-720]
    line_co.set_data(temperature_co_data.index, temperature_co_data['Temperature (Celsius)'])

    #print(temperature_co_data_filtered2)

    now = datetime.now()
    midnight = datetime(now.year, now.month, now.day)
    time_difference = now - midnight
    #hours_since_midngiht = round(time_difference.total_seconds() / 3600, 2) # Ile godzin upłynęło od początku doby
    today_date_date = datetime.strptime(today_date, '%Y-%m-%d').date()
    # Sprawdzenie dnia tygodnia
    if today_date_date.weekday() < 5: # Poniedziałek do piątku (0-4)
        hours_since_midngiht = (time_difference.total_seconds() / 3600) - reduce_hours_days
    else:
        hours_since_midngiht = (time_difference.total_seconds() / 3600) - reduce_hours_weekend
    current_time = datetime.now().strftime('%d-%m %H:%M')
    #print(f"Od początku doby upłynęło {hours_since_midngiht}")


    # Odczyt ostatnich wpisów
    last_row_air = temperature_air_data.iloc[-1]
    last_temperature_air = last_row_air['Temperature (Celsius)']
    last_timestamp_air = last_row_air.name
    last_timestamp_air += timedelta(minutes=5) # Przesunięcie napisu na wykresie
    mean_temperature_air = temperature_air_data['Temperature (Celsius)'].mean()
    mean_temperature_air_day = temperature_air_data_filtered['Temperature (Celsius)'].mean()
    min_temperature_air = temperature_air_data['Temperature (Celsius)'].min()
    max_temperature_air = temperature_air_data['Temperature (Celsius)'].max()
    stopniodni = 16 - mean_temperature_air
    if stopniodni > 0:
        calc_gas_cons = 51.258 * (stopniodni ** 0.424)
    else:
        calc_gas_cons = 0

    last_row_co = temperature_co_data.iloc[-1]
    last_temperature_co = last_row_co['Temperature (Celsius)']
    last_temperature_co1 = last_row_co['Temperature (Celsius)']
    last_timestamp_co1 = last_row_co.name
    last_timestamp_co = last_row_co.name
    last_timestamp_co += timedelta(minutes=5) 
    mean_temperature_co = temperature_co_data_filtered2['Temperature (Celsius)'].mean()
    mean_temperature_co2 = temperature_co_data_filtered4['Temperature (Celsius)'].mean()
    delta_mean_temperature_co = mean_temperature_co - mean_temperature_co2
    
    last_row_co2 = temperature_co_data.iloc[-2]
    last_temperature_co2 = last_row_co2['Temperature (Celsius)']
    last_timestamp_co2 = last_row_co2.name

    last_row_co3 = temperature_co_data.iloc[-3]
    last_temperature_co3 = last_row_co3['Temperature (Celsius)']
    last_timestamp_co3 = last_row_co3.name

    last_row_co4 = temperature_co_data.iloc[-4]
    last_temperature_co4 = last_row_co4['Temperature (Celsius)']
    last_timestamp_co4 = last_row_co4.name

    last_row_co5 = temperature_co_data.iloc[-5]
    last_temperature_co5 = last_row_co5['Temperature (Celsius)']
    last_timestamp_co5 = last_row_co5.name

    last_row_co6 = temperature_co_data.iloc[-6]
    last_temperature_co6 = last_row_co6['Temperature (Celsius)']
    last_timestamp_co6 = last_row_co6.name

    last_row_co7 = temperature_co_data.iloc[-7]
    last_temperature_co7 = last_row_co7['Temperature (Celsius)']
    last_timestamp_co7 = last_row_co7.name

    # Wykrywanie grzania CO
    #print(last_timestamp_co2, last_temperature_co2, last_timestamp_co1, last_temperature_co1)
    #print(last_temperature_co6, last_temperature_co5, last_temperature_co4, last_temperature_co3, last_temperature_co2, last_temperature_co1)

    

    if last_temperature_co7 is not None and last_temperature_co6 is not None and last_temperature_co5 is not None and last_temperature_co4 is not None and last_temperature_co3 is not None and last_temperature_co2 is not None and last_temperature_co1 is not None:
        if last_temperature_co7 < last_temperature_co6 and last_temperature_co6 < last_temperature_co5 and last_temperature_co5 < last_temperature_co4 and last_temperature_co4 < last_temperature_co3 and last_temperature_co3 >= last_temperature_co2 and last_temperature_co2 >= last_temperature_co1:
            last_heat = last_temperature_co2
            last_heat_time = last_timestamp_co2
            #if last_heat != previous_heat: # Sprawdź, czy wartość last_heat się zmieniła
                #print("Last heat:", last_heat)
                #print("previous_heat:", previous_heat)
                #print(heats)
            heats.append(last_heat)
            heat_numbers.append(len(heats)) # dodajemy numer porządkowy czyli liczbę elementów listy heats
            previous_heat = last_heat # Zakutalizuj poprzednią wartość last_heat
            #if last_heat_time != previous_heat_time:
            heat_times.append(last_heat_time)
                #print("Last heat time:", last_heat_time)
                #print("previous_heat_time:", previous_heat_time)
                #print(heat_times)
            previous_heat_time = last_heat_time
            
            update_table(heats, heat_times, heat_numbers, table_axis)

    if not data.empty:
        for i, row in data[:-1].iterrows():  # Skip the last record for duration calculation
            start = row['Datetime']
            if i + 1 < len(data):
               end = data.loc[i + 1, 'Datetime']
               duration = (end - start).total_seconds() / 60.   # Calculate duration in minutes
               

               # Adjust duration based on the state
               if row['State'].lower() == 'turn on':
                   # Reduce duration by 74 seconds (converted to minutes) for "Turn on" cycles
                   adjusted_duration = max(0.2, duration - internet_delay / 60)  # Ensure duration does not go negative
                   turn_on_count += 1
               else:
                   # Increase duration by 40 seconds (converted to minutes) for "Turn off" cycles
                   adjusted_duration = duration + internet_delay / 60
                   turn_off_count += 1
    
               color = 'red' if row['State'].lower() == 'turn on' else 'blue'
               ax1.bar(start, adjusted_duration, width=0.002, color=color, align='edge')
               if color == 'red':
                   total_on_time += adjusted_duration  # Update total_on_time in minutes
                   total_on_count = turn_on_count
                   avg_turn_on_time = total_on_time / total_on_count if total_on_count > 0 else 0
                   formatted_avg_turn_on_time = format_time(avg_turn_on_time)
                   formatted_duration = format_time(adjusted_duration)
                   print(f"Start: {start}, End: {end}, Duration (min): {formatted_duration}, State: {row['State']}")
                   # print(f"Ilość Turn on: {total_on_count} (avg: {formatted_avg_turn_on_time})")
               else:
                   total_off_time += adjusted_duration
                   #print (total_off_time)
                   total_off_count = turn_off_count
                   avg_turn_off_time = (total_off_time - reduction_minutes) / total_off_count if total_off_count > 0 else 0
                   #print (avg_turn_off_time)
                   formatted_avg_turn_off_time = format_time(avg_turn_off_time)
                   formatted_duration = format_time(adjusted_duration)
                   print(f"Start: {start}, End: {end}, Duration (min): {formatted_duration}, State: {row['State']}")
                   # print(f"Ilość Turn off: {total_off_count} (avg: {formatted_avg_turn_off_time})")
               
               last_datetime = row['Datetime']



    # Calculate energy consumption and cost
    total_on_time_min = total_on_time
    now = datetime.now()
    minutes_since_midnight = now.hour * 60 + now.minute # Minuty od początku doby
    minutes_remaining = 1440 - minutes_since_midnight # Minuty do końca doby
    if minutes_since_midnight > 0:
        predicted_total_on_time = (total_on_time_min / minutes_since_midnight) * 1440
    else:
        predicted_total_on_time = total_on_time_min       
    energy_consumption = total_on_time_min * gas_energy * gas_flow # Convert total on time to hours and multiply by energy rate
    
    # Pobranie dzisiejsze daty
    current_date = datetime.now().date()


    #Sprawdzenie, czy today_date jest dzisiejszą datą
    #To jest do rozbudowy
    energy_consumption_hour = (energy_consumption / hours_since_midngiht) - 0.81 # zapotrzebowanie na moc cieplną bez CWU
    energy_cost = energy_consumption * gas_cost  # Calculate cost
    Gas_volume = energy_consumption / gas_energy
    Gazomierz_current = Gas_volume + gazomierz_odczyt
    predicted_total_consumption = predicted_total_on_time * gas_flow * gas_energy
    
    # Update legend with the total on time, energy consumption, and cost
    
   
    teraz = datetime.now()
    if not data.empty:
        last_entry = data.iloc[-1]['Datetime']
        last_state = data.iloc[-1]['State'] 
    else:
        # Tutaj możesz zdefiniować alternatywną logikę na wypadek pustego DataFrame
        # Może to być wartość domyślna, logowanie błędu, wyjątek itp.
        # pass
        last_entry = last_datetime
        print("DataFrame 'data' jest pusty. Odczyt pominięto.")

    # last_entry = data.iloc[-1]['Datetime']  # Dodaj tę linię
    # last_state = data.iloc[-1]['State']    # Ostatni stan
    
    cykl = last_entry - last_datetime
    pauza = datetime.now() - last_entry
    formatted_cykl = format_timedelta(cykl)
    formatted_pauza = format_timedelta(pauza)
    pauza_minuty = pauza.total_seconds() / 60 # Konwersja pauzy na minuty
    current_time =  now.strftime('%H:%M')
    
    if last_state == 'Turn on':
       total_on_time_plus = total_on_time_min + pauza_minuty
    else:
       total_on_time_plus = total_on_time_min 
    if end_time is None:
        temporary_bar(ax1, last_entry, pauza_minuty, last_state)
   
    # Usuwanie starych linii, jeśli istnieją
    # print(f'Liczba obiektów artystycznych przed usunięciem: {len(ax1.lines)}')
    if line_on is not None:
        line_on.remove()
    if line_off is not None:
        line_off.remove()
    if avg_turn_off_text is not None:
        avg_turn_off_text.remove()
    if avg_turn_on_text is not None:
        avg_turn_on_text.remove()
    if text01 is not None:
        text01.remove()
    if text02 is not None:
        text02.remove()
    if text03 is not None:
        text03.remove()
    if text04 is not None:
        text04.remove()
    if text05 is not None:
        text05.remove()

    # print(f'Liczba obiektów artystycznych po usunięciu: {len(ax1.lines)}')    
    
    if(avg_turn_on_time is not None and avg_turn_off_time is not None):
        try:
            # Dodawanie dwóch linii poziomych na całej szerokości wykresu
            line_on = ax1.axhline(y=avg_turn_on_time, color='r', linestyle='--', label='On')
            line_off = ax1.axhline(y=avg_turn_off_time, color='b', linestyle=':', label='Off')
        except UnboundLocalError:
            print('pominięto')
    else:
        print('dupa')

    # Umieszczanie tekstu na wykresie
    avg_time = avg_turn_on_time + avg_turn_off_time
    formatted_avg_time = format_time(avg_time)
    if last_heat_time is not None:
        last_heat_time_formatted = last_heat_time.strftime('%H:%M')
    else:
        last_heat_time_formatted = 'Brak'
    transform_mixed = mtransforms.blended_transform_factory(ax1.transAxes, ax1.transData) # oś x wg wykresu, oś y wg danych
    avg_turn_off_text = ax1.text(0.995, avg_turn_off_time, f'{formatted_avg_turn_off_time} ({turn_off_count})',
        verticalalignment='bottom', horizontalalignment='right',
        transform=transform_mixed , fontsize=12, color='blue',
        fontname='Arial', fontweight='bold')
    avg_turn_on_text = ax1.text(0.995, avg_turn_on_time, f'{formatted_avg_turn_on_time} ({turn_on_count})',
        verticalalignment='bottom', horizontalalignment='right',
        transform=transform_mixed, fontsize=12,color='red',
        fontname='Arial', fontweight='bold')

    # Umieszczanie przykładowego tekstu na wykresie
    # Tutaj trzeba poprawić.
    text01 = ax1.text(0.00, 1.01,
        f'{today_date} {current_time}, ON time: {total_on_time_min:.2f} min, Gas Consumption: {energy_consumption:.1f} kWh ({Gas_volume:.3f} m³) ({Gazomierz_current:.3f}), {energy_cost:.2f} PLN, {energy_consumption_hour:.2f} kW', 
        verticalalignment='bottom', horizontalalignment='left',
        transform=ax1.transAxes, fontsize=12, color='black',
        fontname='Arial Narrow', fontweight='bold')

    text02 = ax1.text(1.00, 1.01,
        f'Air avg: {mean_temperature_air:.1f}°C, day: {mean_temperature_air_day:.1f}°C, (from {min_temperature_air:.1f} to {max_temperature_air:.1f}) {stopniodni:.1f} stopniodni, CGC {predicted_total_consumption:.1f} kWh',
        verticalalignment='bottom', horizontalalignment='right',
        transform=ax1.transAxes, fontsize=12, color='black',
        fontname='Arial Narrow', fontweight='bold')

    text03 = ax1.text(last_timestamp_air, last_temperature_air,
        f'{last_temperature_air:.1f}',
        verticalalignment='center', horizontalalignment='left',
        transform=ax2.transData, fontsize=12, color='orange',
        fontname='Arial Narrow', fontweight='bold')

    text04 = ax1.text(last_timestamp_co, last_temperature_co,
        f'{last_temperature_co:.1f}',
        verticalalignment='center', horizontalalignment='left',
        transform=ax1.transData, fontsize=12, color='brown',
        fontname='Arial Narrow')

    text05 = ax1.text(0.55, 1.01,
        f'Water avg 2h: {mean_temperature_co2:.1f}°C, {mean_temperature_co:.1f}°C, {delta_mean_temperature_co:.1f}, Cycle: {formatted_avg_time}, {last_heat_time_formatted}, {last_heat}', 
        verticalalignment='bottom', horizontalalignment='center',
        transform=ax1.transAxes, fontsize=12, color='brown',
        fontname='Arial', fontweight='bold')

     # Sprawdzenie i zapisanie wykresu, jeśli jest odpowiednia godzina
    
    if end_time is None:
        save_plot_if_time()

    #Kontrola liczba obiektów. Funkcja jest zdefiniowana wcześniej
    #liczba_obiektow = licz_obiekty_na_wykresie(ax1)
    #print("Liczba obiektów na wykresie:", liczba_obiektow)


    #snapshot = tracemalloc.take_snapshot()
    #top_stats = snapshot.statistics('lineno')

    # Czyszczenie terminala przed wyświetleniem nowych wyników
    #os.system('clear')

    #print("[ Top 10 ]")
    #for stat in top_stats[:10]:  # Wyświetl top 10 miejsc alokacji pamięci
    #    print(stat)


    # ax1.legend([
    #   f'Total ON time: {int(total_on_time_min)} min',
    #   f'Total ON time plus: {total_on_time_plus:.2f} min',
    #   f'Gas Consumption: {energy_consumption:.1f} kWh ({Gas_volume:.1f} m³)',
    #   f'Gas Cost: {energy_cost:.2f} PLN'
    # ], loc='upper right')

    #print(f'{last_datetime.strftime("%H:%M")} -> {last_entry.strftime("%H:%M")} ({formatted_cykl}) ({formatted_pauza}) {last_state}')

update(0)
ani = FuncAnimation(fig, update, interval=10000, cache_frame_data=False)  # Refresh every 10 seconds



plt.show()
