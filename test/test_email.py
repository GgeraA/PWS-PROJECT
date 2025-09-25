from utils.email_helper import send_email

if __name__ == "__main__":
    # Cambia este correo al tuyo para probar
    result = send_email(
        "brayangonzalez030405@gmail.com",
        "Prueba de Email",
        "Hola! Este es un correo de prueba desde email_helper 🚀"
    )
    print(result)
