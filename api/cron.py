from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Valores solicitados para compra y venta
valor_solicitado_compra = 900
valor_solicitado_venta = 1000

# Token y Chat ID para enviar mensajes a Telegram
bot_token = '5164767011:AAGyLnpEQnlbjyyeAVdS_9eGrtJfxfODLwI'
bot_chatID = '5234865691'

def telegram_bot_sendtext(bot_message):
    enviar_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={bot_chatID}&parse_mode=Markdown&text={bot_message}'
    try:
        response = requests.get(enviar_text)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje de Telegram: {e}")
        return None

def check_dolar():
    # Obtener valor del dólar desde Google Finance
    try:
        url = requests.get("https://www.google.com/finance/quote/USD-CLP")
        soup = BeautifulSoup(url.content, "html.parser")
        resultado = soup.findAll("div", {"class": "YMlKec fxKbKc"})
        valor_us_google = float(resultado[0].get_text().replace(',', '.'))
    except Exception as e:
        print(f"Error al obtener datos de Google Finance: {e}")
        valor_us_google = "No disponible"

    # Obtener valor desde Banco Central
    valor_bcentral = "No disponible"
    try:
        url = requests.get("https://si3.bcentral.cl/indicadoressiete/secure/indicadoresdiarios.aspx")
        soup = BeautifulSoup(url.content, "html.parser")
        resultado = soup.findAll("label", {"id": "lblValor1_3"})
        convertir_valor = resultado[0].get_text()
        if convertir_valor != 'ND':
            valor_bcentral = float(convertir_valor.replace(',', '.'))
    except Exception as e:
        print(f"Error al obtener datos del Banco Central: {e}")

    # Obtener datos de valoraldia.cl
    try:
        urldl = 'https://valoraldia.cl/dolar/'
        html = requests.get(urldl).content
        dflist = pd.read_html(html)
        df = dflist[0]
        
        if len(df) > 2:
            casacambio = (df.iloc[1, 0], df.iloc[2, 0]) if len(df.columns) > 0 else ("No disponible", "No disponible")
            fecha1 = df.iloc[1, 3] if len(df.columns) > 3 else "No disponible"
            fecha2 = df.iloc[2, 3] if len(df.columns) > 3 else "No disponible"
        else:
            casacambio, fecha1, fecha2 = ("No disponible", "No disponible", "No disponible")
            print("Advertencia: No hay suficientes filas en el DataFrame para obtener datos de valoraldia.cl")
    except Exception as e:
        print(f"Error al obtener datos de valoraldia.cl: {e}")
        casacambio, fecha1, fecha2 = ("No disponible", "No disponible", "No disponible")

    retorno_compra, retorno_venta = [0, 0], [0, 0]

    def valida_dolar(validacion):
        try:
            if int(validacion[:1]) == 1:
                return int(validacion[:1] + validacion[2:5])
            else:
                return int(validacion[0:3])
        except ValueError:
            return 0

    retorno_compra = []
    retorno_venta = []
    for x in [1, 2]:
        try:
            compra = df.iloc[x, 1]
            venta = df.iloc[x, 2]
            valor_compra = compra.split()[0]
            valor_venta = venta.split()[0]
            retorno_compra.append(valida_dolar(valor_compra))
            retorno_venta.append(valida_dolar(valor_venta))
        except IndexError:
            retorno_compra.append(0)
            retorno_venta.append(0)

    def funventa():
        valormax_venta = min(retorno_venta)
        if valormax_venta <= valor_solicitado_venta:
            mensaje = (
                f"¡ATENCIÓN! ES MOMENTO DE INVERTIR.\n"
                f"La Venta de dólar está en: ${valormax_venta}\n\n"
                f"Los Valores en Línea son:\n"
                f"- Google Finance: ${valor_us_google}\n"
                f"- Banco Central: {valor_bcentral}\n\n"
                f"Casa de Cambio Venta Último Cambio\n"
                f"{casacambio[0]} ${retorno_venta[0]} {fecha1}\n"
                f"{casacambio[1]} ${retorno_venta[1]} {fecha2}\n\n"
                f"Nota: Ajusta tu valor de inversión. Venden a: {valor_solicitado_venta}"
            )
            telegram_bot_sendtext(mensaje)

    def funcompra():
        valormax_compra = max(retorno_compra)
        if valormax_compra >= valor_solicitado_compra:
            mensaje = (
                f"El Precio en Línea es:\n\n"
                f"- Google Finance: ${valor_us_google}\n"
                f"- Banco Central: {valor_bcentral}\n\n"
                f"La Compra de dólar está:\n"
                f"- {casacambio[0]} a: ${retorno_compra[0]} - {fecha1}\n"
                f"- {casacambio[1]} a: ${retorno_compra[1]} - {fecha2}\n\n"
                f"La Venta de dólar está:\n"
                f"- {casacambio[0]}: ${retorno_venta[0]} - {fecha1}\n"
                f"- {casacambio[1]}: ${retorno_venta[1]} - {fecha2}\n\n"
                f"Nota: Ajusta tu valor de inversión. Compran a: {valor_solicitado_compra}, Venden a: {valor_solicitado_venta}"
            )
            telegram_bot_sendtext(mensaje)

    funventa()
    funcompra()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        check_dolar()
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Dolar check executed'.encode())
        return
