import pandas as pd
from db.session import sync_engine
from db.models.org_enum import OrgType


TYPE_MAP = {e.value: e.name for e in OrgType}  # "ВУЗ" -> "VUZ"


def import_excel_to_sql(
    excel_path: str,
    sheet_name: str | int = 0,
    table_name: str = "organizations",
    if_exists: str = "append",  # "append" | "replace" | "fail"
    chunk_size: int = 2000,
    drop_duplicates_by_kpp: bool = True,
):
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
    df = df.dropna(how="all")

    if df.empty:
        print("⚠️ Excel пустой — нечего импортировать")
        return

    # убираем мусорные колонки типа Unnamed: 0
    df = df.loc[:, ~df.columns.astype(str).str.contains(r"^Unnamed", na=False)]

    # нормализуем названия колонок
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # если вдруг в Excel есть id — выбрасываем (он автоинкрементный)
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    print(f"📌 Колонки из Excel: {list(df.columns)}")
    print(f"📌 Строк до обработки: {len(df)}")

    # обязательные колонки
    required_cols = ["full_name", "short_name", "kpp", "region", "type"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"❌ В Excel нет обязательных колонок: {missing}")

    # чистка строк: trim + пустые -> None
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            df[col] = df[col].replace("", None)

    # NaN -> None
    df = df.where(pd.notnull(df), None)

    # short_name NOT NULL: если пустой -> full_name
    df["short_name"] = df["short_name"].fillna(df["full_name"])

    # ✅ enum type: "ВУЗ" -> "VUZ"
    df["type"] = df["type"].astype(str).str.strip()
    df["type"] = df["type"].map(TYPE_MAP)

    bad_types = df[df["type"].isna()]
    if not bad_types.empty:
        print("❌ Найдены неизвестные значения type в Excel (пример):")
        print(bad_types[["full_name", "kpp"]].head(15))
        raise ValueError("Исправьте значения в колонке type — они не совпадают с OrgType")

    # kpp -> число
    df["kpp"] = pd.to_numeric(df["kpp"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["kpp"])
    removed = before - len(df)
    if removed:
        print(f"⚠️ Удалено строк без корректного kpp: {removed}")

    df["kpp"] = df["kpp"].astype("int64")

    # float колонки -> float + fill 0
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

    # дубли по kpp внутри Excel
    if drop_duplicates_by_kpp:
        before = len(df)
        df = df.drop_duplicates(subset=["kpp"], keep="first")
        removed = before - len(df)
        if removed:
            print(f"⚠️ Удалено дублей по kpp в Excel: {removed}")

    print(f"✅ Строк после обработки: {len(df)}")

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
