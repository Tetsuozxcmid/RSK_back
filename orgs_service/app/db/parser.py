import pandas as pd
from sqlalchemy import text
from db.session import sync_engine


def import_excel_to_sql(
    excel_path: str,
    sheet_name: str | int = 0,
    table_name: str = "organizations",
    if_exists: str = "append",  # "append" | "replace" | "fail"
    chunk_size: int = 2000,
    drop_duplicates_by_kpp: bool = True,
):
    # 1) Загружаем Excel
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")

    # 2) Удаляем полностью пустые строки
    df = df.dropna(how="all")

    if df.empty:
        print("⚠️ Excel пустой — нечего импортировать")
        return

    # 3) Убираем мусорные колонки типа Unnamed: 0
    df = df.loc[:, ~df.columns.astype(str).str.contains(r"^Unnamed", na=False)]

    # 4) Нормализуем названия колонок
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    print(f"📌 Колонки из Excel: {list(df.columns)}")
    print(f"📌 Строк до обработки: {len(df)}")

    # 5) Проверяем обязательные поля
    required_cols = ["full_name", "short_name", "kpp", "region", "type"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"❌ В Excel нет обязательных колонок: {missing}")

    # 6) Чистим строковые поля: trim + пустые строки -> None
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            df[col] = df[col].replace("", None)

    # 7) NaN -> None (чтобы ушло в SQL как NULL)
    df = df.where(pd.notnull(df), None)

    # 8) short_name обязателен: если пусто -> берём full_name
    df["short_name"] = df["short_name"].fillna(df["full_name"])

    # 9) Приводим kpp к числу (и выкидываем строки где kpp невалидный)
    df["kpp"] = pd.to_numeric(df["kpp"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["kpp"])
    after = len(df)
    if before != after:
        print(f"⚠️ Удалено строк без корректного kpp: {before - after}")

    # kpp -> int (BigInteger)
    df["kpp"] = df["kpp"].astype("int64")

    # 10) Приведение числовых колонок к float + заполнение None -> 0.0
    float_cols = [
        "star",
        "knowledge_skills_z",
        "knowledge_skills_v",
        "digital_env_e",
        "data_protection_z",
        "data_analytics_d",
        "automation_a",
    ]
    for c in float_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0).astype(float)

    # 11) Если нужно — убираем дубликаты по kpp в Excel (иначе упадёте на unique)
    if drop_duplicates_by_kpp:
        before = len(df)
        df = df.drop_duplicates(subset=["kpp"], keep="first")
        removed = before - len(df)
        if removed:
            print(f"⚠️ Удалено дублей по kpp в Excel: {removed}")

    # 12) Отладочный вывод проблемных строк
    bad_short = df[df["short_name"].isna()]
    if not bad_short.empty:
        print("❌ Остались строки без short_name (не должно быть!)")
        print(bad_short[["full_name", "kpp"]].head(10))

    print(f"✅ Строк после обработки: {len(df)}")

    # 13) Загрузка в БД
    with sync_engine.begin() as conn:
        # Если replace — можно перезаписать таблицу
        # df.to_sql сам создаёт таблицу, если её нет, но у вас таблица уже есть -> append норм
        df.to_sql(
            name=table_name,
            con=conn,
            if_exists=if_exists,
            index=False,
            chunksize=chunk_size,
            method="multi",
        )

    print(f"✅ Импорт завершён: {len(df)} строк -> таблица '{table_name}'")
