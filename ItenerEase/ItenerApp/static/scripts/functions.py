from email_validator import validate_email, EmailNotValidError

def check_email(email):
    try:
        v = validate_email(email)
        return True
    except EmailNotValidError as e:
        return False
