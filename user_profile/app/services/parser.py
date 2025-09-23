import pandas as pd
from typing import List,Dict
import os

class OrgsParser:
    def __init__(self):
        self.organizations = []

    def parse_excel(self,file_path: str) -> List[Dict]:
        df = pd.read_excel(file_path)
        org_names = df['Учебное заведение'].dropna().unique().tolist()
        self.organizations = [
                {"id":i,"name":str(name).strip()}
                for i , name in enumerate(org_names,1)
                if str(name).strip()
                ]
        return self.organizations

    def get_organizations(self,skip: int = 0,limit: int = 50,search: str = None) -> Dict:
        data = self.organizations

        if search:
            data = [org for org in data if search.lower() in str(org.get('name','')).lower()]

        total = len(data)
        paginated_data = data[skip:skip + limit]

        return {"organizations":paginated_data}

    def get_all_orgs(self) -> List[Dict]:
        return self.organizations

org_parser = OrgsParser()


