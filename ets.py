from werkzeug.security import check_password_hash

print(check_password_hash('pbkdf2:sha256:600000$Mj22yaSvC9Kv8DV1$4d3bd4dd56cbde38955da99c245d4c136cc81b293b6db547211e392c8a51e752','123321123'))