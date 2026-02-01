import pandas as pd
from db.session import sync_engine
from db.models.org_enum import OrgType


def import_excel_to_sql(
    excel_path: str,
    sheet_name: str | int = 0,
    table_name: str = "organizations",
    if_exists: str = "append",  # "append" | "replace" | "fail"
    chunk_size: int = 2000,
    drop_duplicates_by_inn: bool = True,
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

    # если вдруг в Excel есть id — выкидываем
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    print(f"📌 Колонки из Excel: {list(df.columns)}")
    print(f"📌 Строк до обработки: {len(df)}")

    # 5) Проверяем обязательные поля
    required_cols = ["full_name", "short_name", "inn", "region", "type"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"❌ В Excel нет обязательных колонок: {missing}")

    # 6) Чистим строковые поля: trim + пустые строки -> None
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            df[col] = df[col].replace("", None)

    # 7) NaN -> None
    df = df.where(pd.notnull(df), None)

    # 8) short_name NOT NULL: если пустой -> берём full_name
    df["short_name"] = df["short_name"].fillna(df["full_name"])

    # 9) ENUM type: в БД хранятся русские значения -> оставляем как есть
    df["type"] = df["type"].astype(str).str.strip()

    allowed_types = {e.value for e in OrgType}
    bad_types = df[~df["type"].isin(allowed_types)]
    if not bad_types.empty:
        print("❌ Найдены неизвестные значения type в Excel:")
        print(bad_types[["full_name", "kpp", "type"]].head(20))
        raise ValueError(
            "Исправь значения в колонке type в Excel (они не совпадают с OrgType)"
        )

    # 10) inn -> число
    df["inn"] = pd.to_numeric(df["inn"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["inn"])
    removed = before - len(df)
    if removed:
        print(f"⚠️ Удалено строк без корректного inn: {removed}")

    df["inn"] = df["inn"].astype("int64")

    # 11) float колонки -> float + заполнение None -> 0.0
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

    # 12) дубли по inn внутри Excel
    if drop_duplicates_by_inn:
        before = len(df)
        df = df.drop_duplicates(subset=["inn"], keep="first")
        removed = before - len(df)
        if removed:
            print(f"⚠️ Удалено дублей по inn в Excel: {removed}")

    print(f"✅ Строк после обработки: {len(df)}")

    # 13) Импорт в БД
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
