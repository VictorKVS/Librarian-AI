"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""

from alembic import op
import sqlalchemy as sa
import logging
import alembic

# Проверка версии Alembic
required_version = (1, 7, 0)
current_version = tuple(map(int, alembic.__version__.split('.')))
if current_version < required_version:
    raise RuntimeError(f"Alembic {required_version} or higher is required. Current: {alembic.__version__}")

# Настройка логгирования
logger = logging.getLogger("alembic.runtime.migration")
logger.setLevel(logging.INFO)

${imports if imports else ""}

# Revision identifiers, used by Alembic
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

# --- ОПИСАНИЕ: Действия, выполняемые при обновлении схемы ---
def upgrade():
    logger.info("🆙 Выполняется upgrade: %s", revision)
    ${upgrades if upgrades else "pass"}

# --- ОПИСАНИЕ: Откат изменений (downgrade) ---
def downgrade():
    logger.info("⏪ Выполняется downgrade: %s", revision)
    ${downgrades if downgrades else "pass"}

    "
    Назначение:
Шаблон для автогенерации Alembic-миграций. Используется при команде alembic revision --autogenerate.

Особенности (в этой версии):

📝 Комментарии к upgrade() и downgrade()

📋 Логгирование действий через logging

✅ Проверка минимальной версии Alembic (≥ 1.7.0)

Преимущества:
Повышает читаемость и отладку миграций, помогает соблюдать совместимость и контролировать изменения в БД.
    терь каждая новая миграция будет:

включать логи в upgrade и downgrade

проверять минимально допустимую версию Alembic

генерироваться с понятными заголовками и переменными
    "
