# Ubicación: backend/utilidades/enviador_de_correos.py

import os
import resend
from dotenv import load_dotenv

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

def enviar_correo_notificacion(destinatario: str, asunto: str, contenido_html: str) -> bool:
    if not resend.api_key:
        print("ERROR (EMAIL): La clave de API de Resend no está configurada.")
        return False
    
    try:
        params = {
            "from": "Asistente Legal <consultorio.juridico@asis.jur.com>",  # Tu dominio verificado (cambia "no-replies" por lo que quieras)
            "to": [destinatario],  # Ahora puede ser cualquier email
            "subject": asunto,
            "html": contenido_html,  # O usa "text" para plano
        }
        
        email = resend.Emails.send(params)
        print(f"SUCCESS (EMAIL): Correo enviado a {destinatario}. ID: {email['id']}")
        return True

    except Exception as e:
        print(f"ERROR (EMAIL): No se pudo enviar el correo a {destinatario}. Causa: {e}")
        return False