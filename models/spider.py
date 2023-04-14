from dataclasses import dataclass
from datetime import datetime


@dataclass
class CSARelation:
    '''客户与采集的亚马逊数据关系'''

    customer_id: int
    brand_name: str
    brand_source: str
    create_date: datetime
