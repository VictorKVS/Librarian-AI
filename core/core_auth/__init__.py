# core.core_auth package
#
# Модули для управления аутентификацией и авторизацией пользователей:
#   jwt_handler.py   — генерация и проверка JWT-токенов
#   oauth2.py        — схема OAuth2PasswordBearer, логика выдачи и проверки токенов
#   dependencies.py  — зависимости FastAPI (get_current_user, проверка ролей и прав)