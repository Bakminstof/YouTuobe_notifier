from sqlalchemy import TextClause, text


def on_update_trigger(table_name: str) -> TextClause:
    """
    SQLite trigger on update
    :return: TextClause
    """
    return text(
        f""" 
        CREATE TRIGGER IF NOT EXISTS {table_name}_ON_UPDATE
        AFTER UPDATE ON {table_name}
          BEGIN
            UPDATE {table_name} 
            SET updated_at = CURRENT_TIMESTAMP
            WHERE {table_name}.id = NEW.id;
          END;
        """
    )
