import pandas as pd
from app.db.session import engine  # AsyncEngine


def import_excel_to_sql(
    excel_path: str,
    sheet_name: str | int = 0,
    table_name: str = "organizations",
    if_exists: str = "append",   # "append" | "replace" | "fail"
    chunk_size: int = 2000,
):
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
    df = df.dropna(how="all")

    if df.empty:
        print("⚠️ Excel пустой — нечего импортировать")
        return

    # иногда Excel добавляет лишнюю колонку индекса
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]

    # нормализуем названия колонок
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # NaN -> NULL (чтобы ушло в SQL как NULL)
    df = df.where(pd.notnull(df), None)

    # чистим строковые поля
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    print(f"📌 Колонки из Excel: {list(df.columns)}")
    print(f"📌 Строк к импорту: {len(df)}")

    sync_engine = engine.sync_engine

    with sync_engine.begin() as conn:
        df.to_sql(
            name=table_name,
            con=conn,
            if_exists=if_exists,
            index=False,
            chunksize=chunk_size,
            method="multi",
        )

    print(f"✅ Импорт завершён: {len(df)} строк -> таблица '{table_name}'")


if __name__ == "__main__":
    import_excel_to_sql(
        excel_path="/root//RSK_back/orgs_service/app/db/result_full.xlsx",
        sheet_name="Sheet 1",
        table_name="rsk_organizations"
    )
