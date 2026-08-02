import bcrypt

def hash_password(inp_pass):
    salt=bcrypt.gensalt(rounds=12)
    password=bcrypt.hashpw(inp_pass.encode("utf-8"),salt).decode("utf-8")
    return password

def pass_check(password,db_password):
    test=bcrypt.checkpw(password.encode("utf-8"),db_password.encode("utf-8"))
    return test