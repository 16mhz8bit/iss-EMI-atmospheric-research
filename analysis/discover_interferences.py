import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ast
import math
from scipy.signal import savgol_filter

# Caricamento del file CSV
file_path = 'data.csv'
data = pd.read_csv(file_path)

# Parsing dei dati del magnetometro
def parse_magnetometer_data(data_str):
    try:
        # Convertire la stringa in un dizionario
        magnetometer_dict = ast.literal_eval(data_str)
        return magnetometer_dict['x'], magnetometer_dict['y'], magnetometer_dict['z']
    except (ValueError, SyntaxError, KeyError):
        # Gestione degli errori in caso di formato errato
        return None, None, None

# Applicazione della funzione di parsing alla colonna "Magnetometer"
magnetometer_parsed = data['Magnetometer'].apply(parse_magnetometer_data)
magnetometer_df = pd.DataFrame(magnetometer_parsed.tolist(), columns=['X', 'Y', 'Z'])

# Filtrare eventuali righe con valori nulli (se presenti)
magnetometer_df.dropna(inplace=True)

# Estrazione dei dati dei tre assi in array separati
x_array = magnetometer_df['X'].values
y_array = magnetometer_df['Y'].values
z_array = magnetometer_df['Z'].values

# Calcolo del vettore intero per ciascun punto
vettore_array = [math.sqrt(x**2 + y**2 + z**2) for x, y, z in zip(x_array, y_array, z_array)]

# Generazione dell'array temporale
n_time = np.arange(len(vettore_array))

# Parametri per la linea di fit polinomiale
order = 9  # Grado del polinomio
window = 51  # Dimensione della finestra per il filtro Savitzky-Golay (deve essere dispari)

# Applicazione del fit polinomiale utilizzando il filtro Savitzky-Golay
vettore_fit = savgol_filter(vettore_array, window_length=window, polyorder=order)

# Calcolo della differenza tra vettore e vettore_fit
differenza = vettore_array - vettore_fit #np.abs()
differenza_amp = np.sign(differenza) * (differenza ** 2)

# Creazione della figura con due sottotrame
plt.figure(figsize=(10, 10))

# Primo grafico: Vettore originale e fit polinomiale
ax1 = plt.subplot(2, 1, 1)
plt.plot(n_time, vettore_array, label='VETTORE INTERO')
plt.plot(n_time, vettore_fit, label=f'Fit Polinomiale (ordine={order}, finestra={window})', color='red', linestyle='--')
plt.title('Dati del Magnetometro con Fit Polinomiale')
plt.xlabel('Tempo')
plt.ylabel('Valori del Magnetometro')
plt.legend()

# Secondo grafico: Differenza tra vettore e fit
ax2 = plt.subplot(2, 1, 2)
plt.plot(n_time, differenza_amp, label='Differenza (Vettore - Fit)', color='blue')
plt.title('Differenza tra Vettore Intero e Fit Polinomiale')
plt.xlabel('Tempo')
plt.ylabel('Differenza')
plt.legend()

# Aggiunta della banda colorata verticale
ax2.axvspan(27, 115, color='black', alpha=0.3)

ax2.axvspan(208, 297, color='black', alpha=0.3)

ax2.axvspan(292, 312, color='red', alpha=0.3)

ax2.axvspan(190, 205, color='yellow', alpha=0.3)

ax2.axvspan(330, 340, color='yellow', alpha=0.3)

ax2.axvspan(132, 180, color='green', alpha=0.3)

# Mostra entrambi i grafici
plt.tight_layout()
plt.show()
